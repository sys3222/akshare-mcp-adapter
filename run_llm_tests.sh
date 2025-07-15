#!/bin/bash

# LLM功能测试脚本
# 用于测试LLM智能分析功能的完整性和性能

set -e

# 配置
API_BASE_URL="http://localhost:8000"
TEST_CONFIG_FILE="llm_test_cases.json"
RESULTS_DIR="test_results"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
RESULTS_FILE="$RESULTS_DIR/llm_test_results_$TIMESTAMP.json"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 创建结果目录
mkdir -p $RESULTS_DIR

echo -e "${BLUE}🚀 LLM功能测试开始${NC}"
echo "测试配置文件: $TEST_CONFIG_FILE"
echo "结果保存到: $RESULTS_FILE"
echo "API地址: $API_BASE_URL"
echo "时间戳: $TIMESTAMP"
echo "----------------------------------------"

# 检查服务是否运行
echo -e "${YELLOW}📡 检查服务状态...${NC}"
if ! curl -s "$API_BASE_URL/health" > /dev/null 2>&1; then
    echo -e "${RED}❌ 服务未运行，请先启动服务${NC}"
    echo "启动命令: python main.py 或 uvicorn main:app --reload"
    exit 1
fi
echo -e "${GREEN}✅ 服务运行正常${NC}"

# 获取访问令牌
echo -e "${YELLOW}🔐 获取访问令牌...${NC}"
TOKEN_RESPONSE=$(curl -s -X POST "$API_BASE_URL/api/token" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "username=test_user&password=test_password")

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ 无法获取访问令牌${NC}"
    exit 1
fi

ACCESS_TOKEN=$(echo $TOKEN_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])" 2>/dev/null || echo "")

if [ -z "$ACCESS_TOKEN" ]; then
    echo -e "${RED}❌ 访问令牌获取失败${NC}"
    echo "响应: $TOKEN_RESPONSE"
    exit 1
fi
echo -e "${GREEN}✅ 访问令牌获取成功${NC}"

# 初始化结果文件
cat > $RESULTS_FILE << EOF
{
  "test_session": {
    "timestamp": "$TIMESTAMP",
    "api_base_url": "$API_BASE_URL",
    "test_config": "$TEST_CONFIG_FILE"
  },
  "results": [],
  "summary": {
    "total_tests": 0,
    "passed": 0,
    "failed": 0,
    "errors": 0
  }
}
EOF

# 测试函数
run_test_case() {
    local test_id=$1
    local test_name=$2
    local prompt=$3
    local endpoint=$4
    local use_llm=$5
    
    echo -e "${BLUE}🧪 测试: $test_name${NC}"
    echo "提示: $prompt"
    
    local start_time=$(date +%s.%N)
    
    # 构建请求
    local request_data
    if [ "$endpoint" = "chat" ]; then
        request_data="{\"prompt\": \"$prompt\"}"
    else
        request_data="{\"query\": \"$prompt\"}"
    fi
    
    # 发送请求
    local response=$(curl -s -X POST "$API_BASE_URL/api/llm/$endpoint" \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $ACCESS_TOKEN" \
        -d "$request_data" \
        --max-time 30)
    
    local curl_exit_code=$?
    local end_time=$(date +%s.%N)
    local duration=$(echo "$end_time - $start_time" | bc -l)
    
    # 分析结果
    local status="unknown"
    local error_message=""
    
    if [ $curl_exit_code -ne 0 ]; then
        status="error"
        error_message="网络请求失败"
    elif echo "$response" | grep -q "error\|Error\|ERROR"; then
        status="failed"
        error_message="API返回错误"
    elif [ ${#response} -lt 10 ]; then
        status="failed"
        error_message="响应内容过短"
    else
        status="passed"
    fi
    
    # 输出结果
    case $status in
        "passed")
            echo -e "${GREEN}✅ 通过 (${duration}s)${NC}"
            ;;
        "failed")
            echo -e "${YELLOW}⚠️  失败: $error_message${NC}"
            ;;
        "error")
            echo -e "${RED}❌ 错误: $error_message${NC}"
            ;;
    esac
    
    # 保存详细结果
    local result_entry=$(cat << EOF
{
  "test_id": "$test_id",
  "test_name": "$test_name",
  "prompt": "$prompt",
  "endpoint": "$endpoint",
  "use_llm": $use_llm,
  "status": "$status",
  "duration_seconds": $duration,
  "response_length": ${#response},
  "error_message": "$error_message",
  "timestamp": "$(date -Iseconds)"
}
EOF
)
    
    # 更新结果文件
    python3 << EOF
import json
with open('$RESULTS_FILE', 'r') as f:
    data = json.load(f)
data['results'].append($result_entry)
data['summary']['total_tests'] += 1
if '$status' == 'passed':
    data['summary']['passed'] += 1
elif '$status' == 'failed':
    data['summary']['failed'] += 1
else:
    data['summary']['errors'] += 1
with open('$RESULTS_FILE', 'w') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
EOF
    
    echo ""
}

# 运行基础测试用例
echo -e "${YELLOW}📋 运行基础测试用例...${NC}"

# 测试聊天端点
run_test_case "chat_basic" "基础聊天测试" "分析000001最近的表现" "chat" true
run_test_case "chat_market" "市场分析测试" "今日A股市场表现如何？" "chat" true

# 测试分析端点 (LLM模式)
run_test_case "analyze_llm_stock" "LLM股票分析" "分析000001平安银行最近的表现" "analyze?use_llm=true" true
run_test_case "analyze_llm_comparison" "LLM对比分析" "000001和600519哪个更好？" "analyze?use_llm=true" true

# 测试分析端点 (规则模式)
run_test_case "analyze_rule_stock" "规则股票分析" "分析000001平安银行最近的表现" "analyze?use_llm=false" false
run_test_case "analyze_rule_market" "规则市场分析" "今日市场表现如何？" "analyze?use_llm=false" false

# 测试功能端点
echo -e "${YELLOW}🔍 测试功能端点...${NC}"
capabilities_response=$(curl -s -X GET "$API_BASE_URL/api/llm/capabilities" \
    -H "Authorization: Bearer $ACCESS_TOKEN")

if echo "$capabilities_response" | grep -q "analysis_types"; then
    echo -e "${GREEN}✅ 功能端点正常${NC}"
else
    echo -e "${RED}❌ 功能端点异常${NC}"
fi

# 生成测试报告
echo -e "${YELLOW}📊 生成测试报告...${NC}"

python3 << EOF
import json
from datetime import datetime

with open('$RESULTS_FILE', 'r') as f:
    data = json.load(f)

summary = data['summary']
total = summary['total_tests']
passed = summary['passed']
failed = summary['failed']
errors = summary['errors']

success_rate = (passed / total * 100) if total > 0 else 0

print(f"\\n{'='*50}")
print(f"🎯 LLM功能测试报告")
print(f"{'='*50}")
print(f"测试时间: {data['test_session']['timestamp']}")
print(f"总测试数: {total}")
print(f"通过: {passed} ({passed/total*100:.1f}%)" if total > 0 else "通过: 0")
print(f"失败: {failed} ({failed/total*100:.1f}%)" if total > 0 else "失败: 0")
print(f"错误: {errors} ({errors/total*100:.1f}%)" if total > 0 else "错误: 0")
print(f"成功率: {success_rate:.1f}%")
print(f"\\n详细结果保存在: $RESULTS_FILE")

if success_rate >= 80:
    print("\\n🎉 测试结果良好！")
elif success_rate >= 60:
    print("\\n⚠️  测试结果一般，需要改进")
else:
    print("\\n❌ 测试结果较差，需要重点关注")
EOF

echo -e "${BLUE}🏁 LLM功能测试完成${NC}"
