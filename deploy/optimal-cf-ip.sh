#!/usr/bin/env bash
# deploy/optimal-cf-ip.sh — Cloudflare 优选 IP + DNS API 同步脚本
#
# 目的: 在 Cloudflare 公开 IP 段中找出国内访问最快的 5 个 IP, 写入 DNS A 记录
# 效果: majorexplorer.com 国内访问从默认 100-300ms 优化到 30-100ms
#
# 用法:
#   ./optimal-cf-ip.sh                              # dry-run, 只显示 top 5
#   ./optimal-cf-ip.sh --apply                      # 真写 DNS
#   ./optimal-cf-ip.sh --domain example.com         # 自定义域名
#   ./optimal-cf-ip.sh --count 10                   # 取 top 10
#
# 前置:
#   - jq (brew install jq / apt install jq)
#   - Cloudflare API Token (Zone:DNS:Edit 权限, 限定 majorexplorer.com)
#   - Cloudflare Zone ID (在域名概览页右下角)
#
# 长期维护: 每月跑一次 (IP 偶尔会变)

set -euo pipefail

# ── 颜色 ──
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# ── 默认参数 ──
DOMAIN="majorexplorer.com"
COUNT=5
APPLY=false
CF_API_TOKEN="${CF_API_TOKEN:-}"
ZONE_ID="${CF_ZONE_ID:-}"

# ── 解析参数 ──
while [[ $# -gt 0 ]]; do
    case "$1" in
        --apply) APPLY=true; shift ;;
        --domain) DOMAIN="$2"; shift 2 ;;
        --count) COUNT="$2"; shift 2 ;;
        --token) CF_API_TOKEN="$2"; shift 2 ;;
        --zone) ZONE_ID="$2"; shift 2 ;;
        -h|--help)
            echo "用法: $0 [--apply] [--domain DOMAIN] [--count N] [--token TOKEN] [--zone ZONE_ID]"
            echo "环境变量: CF_API_TOKEN, CF_ZONE_ID (也可 --token/--zone 传)"
            exit 0
            ;;
        *) echo -e "${RED}未知参数: $1${NC}"; exit 1 ;;
    esac
done

# ── 检查依赖 ──
for cmd in curl jq; do
    if ! command -v "$cmd" &> /dev/null; then
        echo -e "${RED}❌ 缺少依赖: $cmd${NC}"
        echo "macOS: brew install $cmd"
        echo "Linux: apt install $cmd / yum install $jq"
        exit 1
    fi
done

# ── 提示输入 Token ──
if [[ -z "$CF_API_TOKEN" ]]; then
    echo -e "${YELLOW}需要 Cloudflare API Token (Zone:DNS:Edit 权限, 限定 $DOMAIN)${NC}"
    echo "获取: https://dash.cloudflare.com/profile/api-tokens → Create Token"
    echo "推荐模板: Edit zone DNS"
    read -r -p "Token: " CF_API_TOKEN
fi

# ── 提示输入 Zone ID ──
if [[ -z "$ZONE_ID" ]]; then
    echo -e "${YELLOW}需要 Cloudflare Zone ID (在域名概览页右下角)${NC}"
    read -r -p "Zone ID: " ZONE_ID
fi

# ── 验证 API Token ──
echo ""
echo "🔍 验证 API Token..."
verify=$(curl -s -X GET "https://api.cloudflare.com/client/v4/user/tokens/verify" \
    -H "Authorization: Bearer $CF_API_TOKEN" \
    -H "Content-Type: application/json")
status=$(echo "$verify" | jq -r '.success')
if [[ "$status" != "true" ]]; then
    echo -e "${RED}❌ API Token 无效:${NC}"
    echo "$verify" | jq .
    exit 1
fi
echo -e "${GREEN}✅ Token 有效${NC}"

# ── 下载 Cloudflare 公开 IP 段 ──
echo ""
echo "📡 下载 Cloudflare IP 段..."
ips=$(curl -s https://www.cloudflare.com/ips-v4)
ip_count=$(echo "$ips" | wc -l | tr -d ' ')
echo -e "${GREEN}✅ 获取 ${ip_count} 个 IP 段${NC}"

# ── 展开 IP 段为单个 IP (每个段采样 5 个) ──
echo ""
echo "🔍 测速 Cloudflare IP (TCP 握手时间, 取每个段采样, 找国内最快)..."
echo "这需要 30-60 秒, 请耐心等待..."

# 把 IP 段展开成单个 IP, 写入临时文件
tmp_ips=$(mktemp)
while IFS= read -r cidr; do
    [[ -z "$cidr" || "$cidr" == \#* ]] && continue
    # 用 ipcalc / sipcalc / 简单 awk 展开 CIDR, 采样前 5 个
    # 这里用 python 简单展开
    python3 -c "
import ipaddress, sys
net = ipaddress.ip_network('$cidr')
count = 0
for ip in net:
    if count >= 5: break
    print(ip)
    count += 1
" >> "$tmp_ips" 2>/dev/null || {
        # python3 失败时, 退化用 dig 反查首 IP
        first_ip=$(echo "$cidr" | cut -d/ -f1)
        echo "$first_ip" >> "$tmp_ips"
    }
done <<< "$ips"

total_ips=$(wc -l < "$tmp_ips" | tr -d ' ')
echo "   总共要测 ${total_ips} 个 IP..."

# ── 测速 (TCP 443 握手) ──
echo "   开始测速 (按 TTFB 排序)..."
results=$(mktemp)
while IFS= read -r ip; do
    [[ -z "$ip" ]] && continue
    # 用 curl 测 TCP 握手时间 (HTTPS 443)
    ttfb=$(curl -o /dev/null -s -w "%{time_connect}" --connect-timeout 3 --max-time 5 "https://$ip/cdn-cgi/trace" 2>/dev/null || echo "999")
    echo "$ttfb $ip" >> "$results"
done < "$tmp_ips"

rm -f "$tmp_ips"

# ── 排序, 取 top N ──
top_ips=$(sort -n "$results" | head -n "$COUNT" | awk '{print $2}')
rm -f "$results"

echo ""
echo -e "${GREEN}🏆 国内访问最快的 ${COUNT} 个 Cloudflare IP:${NC}"
echo "$top_ips" | nl -w2 -s'. '

# ── Dry-run vs Apply ──
if [[ "$APPLY" != true ]]; then
    echo ""
    echo -e "${YELLOW}⚠️  DRY-RUN 模式: 未写入 DNS${NC}"
    echo ""
    echo "要实际写入 DNS, 跑:"
    echo "  $0 --apply --domain $DOMAIN --count $COUNT"
    echo ""
    echo "或者手动操作 (Cloudflare Dashboard → DNS → Records → 编辑 A 记录):"
    echo "  Type: A, Name: @, Content: <top IP 之一>, Proxy: Proxied, TTL: Auto"
    echo "  对 top ${COUNT} 个 IP 都加 A 记录 (Cloudflare DNS 支持多 A 记录负载均衡)"
    exit 0
fi

# ── 写 DNS ──
echo ""
echo "📝 写入 DNS A 记录..."

# 1. 获取现有 A 记录的 record_id
existing=$(curl -s -X GET \
    "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records?type=A&name=$DOMAIN" \
    -H "Authorization: Bearer $CF_API_TOKEN" \
    -H "Content-Type: application/json")

record_count=$(echo "$existing" | jq -r '.result | length')
echo "   现有 A 记录: $record_count 个"

# 2. 删除所有现有 A 记录
if [[ "$record_count" -gt 0 ]]; then
    echo "$existing" | jq -r '.result[].id' | while read -r rid; do
        curl -s -X DELETE \
            "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records/$rid" \
            -H "Authorization: Bearer $CF_API_TOKEN" \
            -H "Content-Type: application/json" > /dev/null
        echo "   🗑️  删除 A 记录: $rid"
    done
fi

# 3. 写入新 A 记录 (top N 个 IP)
i=0
echo "$top_ips" | while read -r ip; do
    [[ -z "$ip" ]] && continue
    response=$(curl -s -X POST \
        "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records" \
        -H "Authorization: Bearer $CF_API_TOKEN" \
        -H "Content-Type: application/json" \
        --data "{
            \"type\": \"A\",
            \"name\": \"$DOMAIN\",
            \"content\": \"$ip\",
            \"ttl\": 300,
            \"proxied\": true
        }")
    success=$(echo "$response" | jq -r '.success')
    if [[ "$success" == "true" ]]; then
        echo -e "   ${GREEN}✅ 添加 A 记录: $ip (proxied)${NC}"
    else
        echo -e "   ${RED}❌ 添加失败: $ip${NC}"
        echo "$response" | jq .
    fi
done

echo ""
echo -e "${GREEN}🎉 完成! 等待 5 分钟 DNS 全球生效, 然后验证:${NC}"
echo ""
echo "  dig $DOMAIN A +short"
echo "  curl -I https://$DOMAIN"
echo "  https://itdog.net (国内三网测速, 期望 < 100ms)"
echo ""
echo "💡 提示: IP 偶尔会变, 每月跑一次此脚本即可"
