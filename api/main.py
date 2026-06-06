"""
api/main.py — FastAPI 后端

启动: uvicorn api.main:app --reload --port 8000
文档: http://localhost:8000/docs
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel, Field

from core.recommender import RecommendRequest, recommend
from core.rank_utils import score_to_rank, rank_to_score
from core.data_loader import (
    get_all_subjects, get_all_years, get_all_xuanke_options, get_all_provinces,
)
from core.equivalent import equivalent_rank_3year
from api.pdf_report import build_pdf_report

app = FastAPI(
    title="高考志愿推荐 API (多省支持)",
    description="基于位次驱动的 N 志愿生成器。当前支持: 湖北 (其它省加数据即可)",
    version="0.2.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ────────────────────────────────────────
# 1. 工具端点
# ────────────────────────────────────────
class ScoreToRankRequest(BaseModel):
    province: str = "hubei"
    score: int
    subject: str
    year: int = 2025


class ScoreToRankResponse(BaseModel):
    province: str
    score: int
    rank: int


@app.post("/api/score-to-rank", response_model=ScoreToRankResponse)
def api_score_to_rank(req: ScoreToRankRequest):
    """分数 → 位次"""
    try:
        rank = score_to_rank(req.score, req.province, req.subject, req.year)
        return ScoreToRankResponse(province=req.province, score=req.score, rank=rank)
    except Exception as e:
        raise HTTPException(500, str(e))


class RankToScoreRequest(BaseModel):
    province: str = "hubei"
    rank: int
    subject: str
    year: int = 2025


class RankToScoreResponse(BaseModel):
    province: str
    rank: int
    score: int


@app.post("/api/rank-to-score", response_model=RankToScoreResponse)
def api_rank_to_score(req: RankToScoreRequest):
    """位次 → 分数"""
    try:
        score = rank_to_score(req.rank, req.province, req.subject, req.year)
        return RankToScoreResponse(province=req.province, rank=req.rank, score=score)
    except Exception as e:
        raise HTTPException(500, str(e))


class EquivalentRequest(BaseModel):
    province: str = "hubei"
    rank: int
    subject: str


class EquivalentResponse(BaseModel):
    province: str
    rank: int
    subject: str
    equivalent_scores: dict   # {2023: 580, 2024: 575, ...}


@app.post("/api/equivalent", response_model=EquivalentResponse)
def api_equivalent(req: EquivalentRequest):
    """等效分换算(看 3 年分数对照)"""
    try:
        scores = equivalent_rank_3year(req.province, req.subject, 2025, req.rank)
        return EquivalentResponse(
            province=req.province, rank=req.rank, subject=req.subject,
            equivalent_scores=scores,
        )
    except Exception as e:
        raise HTTPException(500, str(e))


@app.get("/api/meta")
def api_meta(province: str = "hubei"):
    """元信息:可用的省份/科类/选科/年份"""
    return {
        "provinces": get_all_provinces(),
        "subjects": get_all_subjects(province),
        "years": sorted(set(get_all_years(province))),
        "xuanke_options": get_all_xuanke_options(province),
        "current_province": province,
    }


# ────────────────────────────────────────
# 2. 主推荐端点
# ────────────────────────────────────────
@app.post("/api/recommend")
def api_recommend(req: RecommendRequest):
    """N 志愿推荐(多省支持)"""
    try:
        response = recommend(req)
        return response.model_dump()
    except FileNotFoundError as e:
        raise HTTPException(404, f"数据缺失: {str(e)}。请先运行: python scripts/fetch_real_data.py --province {req.province}")
    except Exception as e:
        raise HTTPException(500, str(e))


@app.post("/api/recommend/pdf")
def api_recommend_pdf(req: RecommendRequest):
    """生成 96 志愿 PDF 报告 (application/pdf)"""
    import traceback
    try:
        response = recommend(req)
        pdf_bytes = build_pdf_report(req, response)
        # 用纯 ASCII 文件名,避免 latin-1 编码错误
        ascii_prov = {
            "hubei": "hubei", "guangdong": "guangdong", "jiangsu": "jiangsu",
        }.get(req.province, "other")
        ascii_subj = "physics" if req.subject == "物理" else "history"
        filename = f"volunteer_report_{ascii_prov}_{ascii_subj}_{req.year}.pdf"
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
            },
        )
    except FileNotFoundError as e:
        raise HTTPException(404, f"数据缺失: {str(e)}")
    except Exception as e:
        # 把错误信息打到 stderr,方便 debug
        print("PDF generation error:", file=__import__("sys").stderr)
        traceback.print_exc()
        raise HTTPException(500, f"PDF 生成失败: {type(e).__name__}: {str(e)[:200]}")


# ────────────────────────────────────────
# 3. 静态前端
# ────────────────────────────────────────
FRONTEND_DIR = Path(__file__).parent.parent / "frontend"
if (FRONTEND_DIR / "index.html").exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

    @app.get("/")
    def serve_index():
        return FileResponse(str(FRONTEND_DIR / "index.html"))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
