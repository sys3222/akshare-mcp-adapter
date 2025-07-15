#!/bin/bash

# 设置夜间数据更新的定时任务
# 每天凌晨2点执行数据更新

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
PYTHON_PATH=$(which python3)

echo "设置夜间数据更新定时任务..."
echo "项目目录: $PROJECT_DIR"
echo "Python路径: $PYTHON_PATH"

# 创建日志目录
mkdir -p "$PROJECT_DIR/logs"

# 生成crontab条目
CRON_JOB="0 2 * * * cd $PROJECT_DIR && $PYTHON_PATH scripts/nightly_cache_update.py >> logs/nightly_update.log 2>&1"

# 检查是否已存在相同的定时任务
if crontab -l 2>/dev/null | grep -q "nightly_cache_update.py"; then
    echo "定时任务已存在，正在更新..."
    # 移除旧的任务
    crontab -l 2>/dev/null | grep -v "nightly_cache_update.py" | crontab -
fi

# 添加新的定时任务
(crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -

echo "✅ 定时任务设置完成!"
echo "任务详情: 每天凌晨2点执行数据更新"
echo "日志文件: $PROJECT_DIR/logs/nightly_update.log"
echo ""
echo "当前定时任务列表:"
crontab -l

echo ""
echo "手动测试命令:"
echo "cd $PROJECT_DIR && $PYTHON_PATH scripts/nightly_cache_update.py"
