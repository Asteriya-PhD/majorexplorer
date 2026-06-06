#!/bin/bash
# scripts/install_cron_6_25.sh — 安装 6/25 自动抓取 cron job
# 用途: 每年 6/25 出分后,自动跑 fetch_real_data.py 抓当年真实数据
#
# macOS 推荐用 launchd(系统 cron 已废弃),本脚本同时给出两种方案
# Linux 走 crontab
#
# 安装: chmod +x scripts/install_cron_6_25.sh && ./scripts/install_cron_6_25.sh
# 卸载: ./scripts/install_cron_6_25.sh uninstall

set -e

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PYTHON_BIN="/tmp/gkvenv/bin/python"  # 改成你的 venv 路径
LOG_DIR="$PROJECT_DIR/data/_logs"
YEAR=$(date +%Y)

mkdir -p "$LOG_DIR"

PLIST_NAME="com.gaokao.fetch_real_data"
PLIST_PATH="$HOME/Library/LaunchAgents/${PLIST_NAME}.plist"

case "${1:-install}" in
    install)
        if [[ "$OSTYPE" == "darwin"* ]]; then
            # macOS launchd
            cat > "$PLIST_PATH" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>${PLIST_NAME}</string>
    <key>ProgramArguments</key>
    <array>
        <string>${PYTHON_BIN}</string>
        <string>${PROJECT_DIR}/scripts/fetch_real_data.py</string>
        <string>--year</string>
        <string>${YEAR}</string>
        <string>--all</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Month</key>
        <integer>6</integer>
        <key>Day</key>
        <integer>25</integer>
        <key>Hour</key>
        <integer>2</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    <key>StandardOutPath</key>
    <string>${LOG_DIR}/fetch_${YEAR}_out.log</string>
    <key>StandardErrorPath</key>
    <string>${LOG_DIR}/fetch_${YEAR}_err.log</string>
    <key>WorkingDirectory</key>
    <string>${PROJECT_DIR}</string>
    <key>RunAtLoad</key>
    <false/>
</dict>
</plist>
EOF
            launchctl load "$PLIST_PATH"
            echo "✅ macOS launchd 已安装: $PLIST_PATH"
            echo "   每年 6/25 凌晨 2:00 自动跑"
            echo "   查看: launchctl list | grep gaokao"
            echo "   日志: $LOG_DIR/fetch_${YEAR}_*.log"
        else
            # Linux crontab
            CRON_LINE="0 2 25 6 * cd $PROJECT_DIR && $PYTHON_BIN scripts/fetch_real_data.py --year $YEAR --all >> $LOG_DIR/cron.log 2>&1"
            (crontab -l 2>/dev/null | grep -v "fetch_real_data" ; echo "$CRON_LINE") | crontab -
            echo "✅ Linux crontab 已安装"
            echo "   $CRON_LINE"
            echo "   查看: crontab -l"
        fi
        ;;

    uninstall)
        if [[ "$OSTYPE" == "darwin"* ]]; then
            launchctl unload "$PLIST_PATH" 2>/dev/null || true
            rm -f "$PLIST_PATH"
            echo "✅ launchd job 已卸载"
        else
            (crontab -l 2>/dev/null | grep -v "fetch_real_data") | crontab -
            echo "✅ crontab 已移除"
        fi
        ;;

    test)
        echo "🧪 立刻测试一次 (year=$YEAR)..."
        "$PYTHON_BIN" "$PROJECT_DIR/scripts/fetch_real_data.py" --year "$YEAR" --all
        ;;

    *)
        echo "Usage: $0 {install|uninstall|test}"
        exit 1
        ;;
esac
