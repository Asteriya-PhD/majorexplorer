/* ─────────────────────────────────────────────
   Mobile data-loader — 拉 manifest + 主数据
   比 PC 轻: 不需要 IDB 缓存, mobile 一次性载入
   ───────────────────────────────────────────── */

const M = (window.MobileData = {
  manifest: null,
  manifestBy: {},
  manifestBySlug: {},
  hierarchy: null,
  strategy: null,
  ready: null,

  async init() {
    if (this.ready) return this.ready;
    this.ready = (async () => {
      const [m, h, s] = await Promise.all([
        fetch("/data/manifest.json").then(r => r.json()),
        fetch("/data/discipline_hierarchy.json").then(r => r.json()).catch(() => null),
        fetch("/data/strategy_industries.json").then(r => r.json()).catch(() => null),
      ]);
      this.manifest = m;
      this.hierarchy = h;
      this.strategy = s;
      for (const maj of m.majors) {
        this.manifestBySlug[maj.slug] = maj;
        const d = maj.discipline || "_";
        (this.manifestBy[d] = this.manifestBy[d] || []).push(maj);
      }
      // 兼容多种 hierarchy key 命名 (disciplines / 门类 / menjia)
      // 实测 public/data/discipline_hierarchy.json 结构:
      //   门类 = {"01": {name, icon, sub_classes: {"0101": {name, majors: [...]}}}, ...}
      if (this.hierarchy) {
        let list = this.hierarchy.disciplines || this.hierarchy.menjia || null;
        const menjaDict = this.hierarchy["门类"];
        if (!list && menjaDict) {
          list = Object.entries(menjaDict).map(([code, v]) => {
            // sub_classes 也是 dict
            const subRaw = v.sub_classes || v.sub || v["大类"] || {};
            const sub = Array.isArray(subRaw) ? subRaw : Object.entries(subRaw).map(([k, sv]) => ({
              code: k,
              name: sv.name || "",
              majors: sv.majors || [],
              total: (sv.majors || []).length,
            }));
            return { code, name: v.name, total: sub.reduce((a, s) => a + (s.total || 0), 0), sub };
          });
        }
        if (!list) list = [];
        this.hierarchy.disciplines = list.map(d => ({
          code: d.code || d["代码"] || "",
          name: d.name || d["名称"] || "",
          total: d.total || d["专业总数"] || 0,
          sub: Array.isArray(d.sub) ? d.sub : Object.entries(d.sub || {}).map(([k, sv]) => ({
            code: k, name: sv.name || "", majors: sv.majors || [], total: (sv.majors || []).length,
          })),
        }));
      }
    })();
    return this.ready;
  },

  // ───── helpers ─────
  styleColor(style) {
    const map = {
      finance: "#4A4564", business: "#5A4632", law: "#3A3A3A",
      gongan: "#1E3A5F", administration: "#5C5C8A", education: "#5C7C4A",
      humanities: "#6B4F35", arts: "#8B3A62", sci: "#1E5E72",
      eng: "#5B5B47", cs: "#1E5E72", medicine: "#8B2424", agri: "#6B7A3F",
    };
    return map[style] || "#4A4564";
  },

  ghost(title) {
    return (title || "?").slice(0, 1);
  },
});

document.addEventListener("DOMContentLoaded", () => M.init());
