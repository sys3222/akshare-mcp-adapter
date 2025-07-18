"""
LLM智能分析处理器
集成真实LLM模型，实现智能金融数据分析和建议生成
支持基于规则的本地分析和基于LLM的智能分析两种模式
"""

import json
import logging
import re
import os
from typing import Dict, Any, List, Optional, Tuple, Union
import pandas as pd
import numpy as np

# LLM相关导入
try:
    import google.generativeai as genai
    from google.generativeai.types import (
        GenerationConfig, Tool, FunctionDeclaration,
        HarmCategory, HarmBlockThreshold, Part
    )
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False
    print("Warning: Google Generative AI not available. Using rule-based analysis only.")

from core.mcp_protocol import MCPRequest
from handlers.mcp_handler import handle_mcp_data_request, _get_and_normalize_akshare_data
from models.schemas import PaginatedDataResponse, IntentType, AnalysisContext, AnalysisResult

logger = logging.getLogger("mcp-unified-service")

# 配置详细的日志格式
def setup_llm_logging():
    """设置LLM模块的详细日志"""
    llm_logger = logging.getLogger("llm_handler")
    if not llm_logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        )
        handler.setFormatter(formatter)
        llm_logger.addHandler(handler)
        llm_logger.setLevel(logging.INFO)
    return llm_logger

llm_logger = setup_llm_logging()

# --- LLM配置和工具定义 ---

def configure_llm():
    """配置LLM模型"""
    if not LLM_AVAILABLE:
        return False

    try:
        gemini_api_key = os.environ.get("GEMINI_API_KEY")
        if not gemini_api_key:
            logger.warning("GEMINI_API_KEY not found in environment. LLM features disabled.")
            return False

        genai.configure(api_key=gemini_api_key)
        logger.info("LLM (Gemini) configured successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to configure LLM: {e}")
        return False

# 改进的LLM配置（借鉴旧版本）
def get_enhanced_generation_config():
    """获取增强的生成配置"""
    if not LLM_AVAILABLE:
        return None

    return GenerationConfig(
        temperature=0.1,  # 更低的温度，更稳定的金融分析
        top_p=0.95,
        top_k=64,
        max_output_tokens=8192,  # 更大的输出限制
        response_mime_type="text/plain",
    )

def get_safety_settings():
    """获取安全设置"""
    if not LLM_AVAILABLE:
        return None

    return {
        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
    }

# 定义AkShare数据获取工具
def create_akshare_tool():
    """创建AkShare数据获取工具定义"""
    get_akshare_data_func = FunctionDeclaration(
        name="get_akshare_data",
        description="根据接口名称和参数从AkShare获取中国金融市场数据。支持股票、基金、指数、宏观经济等各类数据。",
        parameters={
            "type": "object",
            "properties": {
                "interface": {
                    "type": "string",
                    "description": "要调用的AkShare接口名称。例如: 'stock_zh_a_hist'(A股历史数据), 'stock_zh_a_spot_em'(A股实时数据), 'index_zh_a_hist'(指数数据), 'macro_china_gdp'(GDP数据)等。",
                },
                "params": {
                    "type": "object",
                    "description": "接口所需参数的字典。例如: {'symbol': '000001', 'period': 'daily', 'start_date': '20240101', 'end_date': '20241231'}",
                },
            },
            "required": ["interface", "params"],
        },
    )

    return Tool(function_declarations=[get_akshare_data_func])

def load_and_format_interfaces():
    """加载并格式化接口描述供LLM使用"""
    try:
        with open("akshare_interfaces.json", "r", encoding="utf-8") as f:
            interfaces = json.load(f)

        formatted_string = "可用的AkShare接口列表如下，请根据用户问题选择最合适的接口：\n\n"
        for endpoint in interfaces.get("endpoints", []):
            name = endpoint.get("name")
            description = endpoint.get("description")
            params = endpoint.get("input", {})
            param_str = ", ".join([f"{k}: {v}" for k, v in params.items()])
            formatted_string += f"- 接口: '{name}'\n"
            formatted_string += f"  描述: {description}\n"
            if param_str:
                formatted_string += f"  参数: {param_str}\n"
            formatted_string += "\n"
        return formatted_string
    except Exception as e:
        logger.error(f"Error loading interfaces: {e}")
        return "无法加载接口列表。\n"

def get_enhanced_system_instructions():
    """获取增强的系统指令（借鉴旧版本的优秀设计）"""
    tool_descriptions = load_and_format_interfaces()

    return f"""你是一个专业的中国金融市场数据分析助手。你的任务是帮助用户获取和分析金融数据。

**核心职责：**
1. **理解用户需求** - 准确识别用户想要的具体金融数据类型
2. **选择合适接口** - 从下面的AkShare接口列表中选择最适合的接口
3. **构建参数字典** - 为选定的接口构建正确的参数
4. **调用数据工具** - 使用get_akshare_data工具获取数据
5. **专业分析** - 对获取的数据进行专业的金融分析
6. **提供建议** - 基于数据分析给出投资建议和风险提示

**分析原则：**
- 保持客观和专业的分析态度
- 基于数据事实进行分析，避免主观臆测
- 提供具体的数字和比例支持结论
- 明确指出数据的时间范围和局限性
- 给出风险提示和投资建议时要谨慎

**可用的AkShare接口：**
{tool_descriptions}

**重要提醒：**
- 如果工具返回数据，请进行深入的专业分析
- 如果工具返回错误，请清楚地告知用户并建议替代方案
- 始终以用户的投资安全为首要考虑
"""

# 全局LLM配置状态
LLM_CONFIGURED = configure_llm() if LLM_AVAILABLE else False

# 类定义已从models.schemas导入

class LLMAnalysisHandler:
    """增强的LLM智能分析处理器

    支持两种分析模式：
    1. 基于规则的本地分析（快速、离线）
    2. 基于LLM的智能分析（强大、需要API）
    """

    def __init__(self, use_llm: bool = True):
        self.use_llm = use_llm and LLM_CONFIGURED
        self.intent_patterns = self._load_intent_patterns()
        self.analysis_templates = self._load_analysis_templates()
        self._last_context = None

        # LLM相关配置
        if self.use_llm:
            self.akshare_tool = create_akshare_tool()
            self.model_name = "gemini-1.5-flash-latest"
            logger.info("LLM分析模式已启用")
        else:
            logger.info("使用基于规则的分析模式")
    
    def _load_intent_patterns(self) -> Dict[IntentType, List[str]]:
        """加载意图识别模式"""
        return {
            IntentType.STOCK_ANALYSIS: [
                r"分析.*?([0-9]{6})",
                r"([0-9]{6}).*?怎么样",
                r"([0-9]{6}).*?表现",
                r"查看.*?([0-9]{6})",
                r"([\u4e00-\u9fa5]+).*?股票.*?分析",
                r"分析.*?([\u4e00-\u9fa5]+银行)",
                r"([0-9]{6}).*?值得.*?投资",
                r"([\u4e00-\u9fa5]+).*?([0-9]{6})"
            ],
            IntentType.MARKET_OVERVIEW: [
                r"市场.*?概况",
                r"大盘.*?情况",
                r"整体.*?市场",
                r"今日.*?行情",
                r"市场.*?表现"
            ],
            IntentType.FINANCIAL_METRICS: [
                r"财务.*?指标",
                r"PE.*?ROE",
                r"PE.*?PB",
                r"市盈率",
                r"净资产收益率",
                r"ROE",
                r"财报.*?数据",
                r"([0-9]{6}).*?PE.*?ROE",
                r"([0-9]{6}).*?财务",
                r"([0-9]{6}).*?的.*?PE.*?ROE"
            ],
            IntentType.TREND_ANALYSIS: [
                r"趋势.*?分析",
                r"走势.*?如何",
                r"技术.*?分析",
                r"未来.*?走向",
                r"预测.*?走势"
            ],
            IntentType.COMPARISON_ANALYSIS: [
                r"对比.*?([0-9]{6}).*?([0-9]{6})",
                r"比较.*?([0-9]{6}).*?([0-9]{6})",
                r"([0-9]{6}).*?vs.*?([0-9]{6})",
                r"哪个.*?更好",
                r"对比分析.*?([0-9]{6})",
                r"帮我.*?对比.*?([0-9]{6}).*?([0-9]{6})",
                r"([0-9]{6}).*?和.*?([0-9]{6}).*?哪个.*?值得"
            ],
            IntentType.INVESTMENT_ADVICE: [
                r"推荐.*?股票",
                r"买入.*?建议",
                r"投资.*?建议",
                r"应该.*?买",
                r"值得.*?投资"
            ],
            IntentType.RISK_ASSESSMENT: [
                r"风险.*?评估",
                r"风险.*?如何",
                r"安全.*?吗",
                r"风险.*?大吗",
                r"投资.*?风险"
            ]
        }
    
    def _load_analysis_templates(self) -> Dict[IntentType, Dict[str, Any]]:
        """加载分析模板"""
        return {
            IntentType.STOCK_ANALYSIS: {
                "required_data": ["stock_zh_a_hist", "stock_zh_a_spot_em"],
                "analysis_points": [
                    "价格趋势分析",
                    "成交量分析", 
                    "技术指标分析",
                    "相对强弱分析"
                ],
                "risk_factors": ["波动率", "流动性", "基本面风险"]
            },
            IntentType.MARKET_OVERVIEW: {
                "required_data": ["stock_zh_a_spot_em", "index_zh_a_hist"],
                "analysis_points": [
                    "市场整体表现",
                    "行业分布",
                    "涨跌比例",
                    "成交量分析"
                ],
                "risk_factors": ["系统性风险", "市场情绪"]
            },
            IntentType.FINANCIAL_METRICS: {
                "required_data": ["stock_yjbb_em", "stock_financial_abstract"],
                "analysis_points": [
                    "盈利能力分析",
                    "偿债能力分析",
                    "运营效率分析",
                    "成长性分析"
                ],
                "risk_factors": ["财务风险", "经营风险"]
            }
        }
    
    async def analyze_query(self, query: str, username: str = None) -> AnalysisResult:
        """分析用户查询并返回智能分析结果"""
        try:
            if self.use_llm:
                # 使用LLM进行智能分析
                return await self._analyze_with_llm(query, username)
            else:
                # 使用基于规则的分析
                return await self._analyze_with_rules(query, username)

        except Exception as e:
            logger.error(f"分析过程出错: {e}")
            return AnalysisResult(
                summary="分析过程中出现错误，请稍后重试",
                insights=["数据获取失败"],
                recommendations=["请检查查询参数"],
                data_points={},
                charts_suggested=[],
                risk_level="未知",
                confidence=0.0
            )

    async def _analyze_with_llm(self, query: str, username: str = None) -> AnalysisResult:
        """使用LLM进行智能分析（借鉴旧版本的优秀设计）"""
        try:
            # 使用增强的配置创建模型
            model = genai.GenerativeModel(
                model_name="gemini-1.5-pro-latest",  # 使用更强大的Pro模型
                generation_config=get_enhanced_generation_config(),
                safety_settings=get_safety_settings(),
                tools=[self.akshare_tool],
                system_instruction=get_enhanced_system_instructions()
            )

            # 使用聊天会话管理（借鉴旧版本）
            chat_session = model.start_chat()

            # 发送用户查询到LLM
            response = chat_session.send_message(query)

            # 检查是否需要调用工具（借鉴旧版本的优秀设计）
            if response.function_calls:
                tool_call = response.function_calls[0]

                if tool_call.name == "get_akshare_data":
                    interface = tool_call.args.get("interface")
                    params = tool_call.args.get("params", {})

                    logger.info(f"LLM请求调用工具: interface={interface}, params={params}")

                    if not interface:
                        raise ValueError("LLM未提供接口名称")

                    # 调用实际的数据获取函数
                    try:
                        tool_result = await _get_and_normalize_akshare_data(interface, params)

                        # 限制返回给LLM的数据量
                        if isinstance(tool_result, list) and len(tool_result) > 50:
                            tool_result = tool_result[:50] + [{"message": "... (数据已截断，仅显示前50条)"}]

                    except Exception as e:
                        error_message = f"数据获取失败: {str(e)}"
                        logger.error(error_message)
                        tool_result = {"error": error_message}

                    # 发送工具结果回LLM（使用旧版本的方法）
                    response = chat_session.send_message(
                        Part.from_function_response(
                            name="get_akshare_data",
                            response={"data": tool_result},
                        )
                    )

                final_text = response.text
            else:
                # 无需工具调用，直接返回LLM响应
                final_text = response.text

            # 解析LLM响应并构建结构化结果
            return self._parse_llm_response(final_text, query)

        except Exception as e:
            logger.error(f"LLM分析失败: {e}")
            # 回退到基于规则的分析
            return await self._analyze_with_rules(query, username)

    async def _analyze_with_rules(self, query: str, username: str = None) -> AnalysisResult:
        """使用基于规则的分析（原有逻辑）"""
        # 1. 意图识别
        context = self._identify_intent(query)
        self._last_context = context
        logger.info(f"识别意图: {context.intent.value}, 置信度: {context.confidence}")

        # 2. 获取相关数据
        data_responses = await self._fetch_relevant_data(context, username)

        # 3. 数据分析
        analysis_result = await self._analyze_data(context, data_responses)

        # 4. 生成建议
        analysis_result = self._generate_recommendations(context, analysis_result)

        return analysis_result

    def _parse_llm_response(self, llm_text: str, original_query: str) -> AnalysisResult:
        """解析LLM响应并构建结构化结果"""
        try:
            # 尝试从LLM响应中提取结构化信息
            insights = []
            recommendations = []
            data_points = {}
            charts_suggested = []
            risk_level = "中等风险"

            # 简单的文本解析逻辑
            lines = llm_text.split('\n')
            current_section = None

            for line in lines:
                line = line.strip()
                if not line:
                    continue

                # 识别不同的部分
                if any(keyword in line for keyword in ['分析', '洞察', '发现']):
                    current_section = 'insights'
                elif any(keyword in line for keyword in ['建议', '推荐', '策略']):
                    current_section = 'recommendations'
                elif any(keyword in line for keyword in ['风险', '风险等级']):
                    if '高风险' in line:
                        risk_level = "高风险"
                    elif '低风险' in line:
                        risk_level = "低风险"
                    else:
                        risk_level = "中等风险"

                # 提取要点
                if line.startswith(('•', '-', '*', '1.', '2.', '3.')):
                    content = re.sub(r'^[•\-*\d\.]\s*', '', line)
                    if current_section == 'insights':
                        insights.append(content)
                    elif current_section == 'recommendations':
                        recommendations.append(content)

            # 如果没有提取到结构化信息，使用整个响应作为摘要
            if not insights and not recommendations:
                insights = [llm_text[:200] + "..." if len(llm_text) > 200 else llm_text]

            # 根据查询内容建议图表类型
            if any(keyword in original_query for keyword in ['股票', '价格', '走势']):
                charts_suggested = ["价格走势图", "成交量图"]
            elif any(keyword in original_query for keyword in ['市场', '大盘']):
                charts_suggested = ["市场热力图", "行业分布图"]
            elif any(keyword in original_query for keyword in ['财务', 'PE', 'PB']):
                charts_suggested = ["财务指标图", "估值对比图"]

            return AnalysisResult(
                summary=llm_text[:300] + "..." if len(llm_text) > 300 else llm_text,
                insights=insights[:5],  # 限制数量
                recommendations=recommendations[:5],
                data_points=data_points,
                charts_suggested=charts_suggested,
                risk_level=risk_level,
                confidence=0.9  # LLM分析的置信度较高
            )

        except Exception as e:
            logger.error(f"解析LLM响应失败: {e}")
            return AnalysisResult(
                summary=llm_text,
                insights=["LLM分析完成"],
                recommendations=["请参考分析内容"],
                data_points={},
                charts_suggested=[],
                risk_level="未知",
                confidence=0.7
            )
    
    def _identify_intent(self, query: str) -> AnalysisContext:
        """识别用户意图"""
        best_intent = IntentType.UNKNOWN
        best_confidence = 0.0
        entities = {}
        
        for intent_type, patterns in self.intent_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, query, re.IGNORECASE)
                if match:
                    confidence = 0.8  # 基础置信度
                    
                    # 提取实体
                    if match.groups():
                        entities.update({
                            f"entity_{i}": group 
                            for i, group in enumerate(match.groups()) if group
                        })
                        confidence += 0.1  # 有实体提取加分
                    
                    if confidence > best_confidence:
                        best_confidence = confidence
                        best_intent = intent_type
        
        # 提取股票代码
        stock_codes = re.findall(r'\b([0-9]{6})\b', query)
        if stock_codes:
            entities['stock_codes'] = stock_codes
        
        # 提取时间范围
        time_patterns = [
            r'(\d{4})年',
            r'最近(\d+)天',
            r'近(\d+)个月',
            r'今年',
            r'去年'
        ]
        
        for pattern in time_patterns:
            match = re.search(pattern, query)
            if match:
                entities['time_range'] = match.group()
                break
        
        return AnalysisContext(
            intent=best_intent,
            entities=entities,
            confidence=best_confidence,
            raw_query=query
        )
    
    async def _fetch_relevant_data(self, context: AnalysisContext, username: str) -> List[PaginatedDataResponse]:
        """根据意图获取相关数据"""
        data_responses = []
        
        # 根据意图类型确定需要的数据
        template = self.analysis_templates.get(context.intent, {})
        required_interfaces = template.get("required_data", [])
        
        # 如果有股票代码，获取股票数据
        if 'stock_codes' in context.entities:
            for stock_code in context.entities['stock_codes']:
                for interface in required_interfaces:
                    try:
                        request = MCPRequest(
                            interface=interface,
                            params=self._build_params(interface, stock_code, context),
                            request_id=f"llm_analysis_{interface}_{stock_code}"
                        )
                        
                        response = await handle_mcp_data_request(request, 1, 100, username)
                        data_responses.append(response)
                        
                    except Exception as e:
                        logger.warning(f"获取数据失败 {interface}: {e}")
        
        # 如果是市场概览，获取市场数据
        elif context.intent == IntentType.MARKET_OVERVIEW:
            try:
                request = MCPRequest(
                    interface="stock_zh_a_spot_em",
                    params={},
                    request_id="llm_analysis_market_overview"
                )
                response = await handle_mcp_data_request(request, 1, 100, username)
                data_responses.append(response)
            except Exception as e:
                logger.warning(f"获取市场数据失败: {e}")
        
        return data_responses
    
    def _build_params(self, interface: str, stock_code: str, context: AnalysisContext) -> Dict[str, Any]:
        """构建接口参数"""
        params = {}
        
        if interface == "stock_zh_a_hist":
            params = {
                "symbol": stock_code,
                "period": "daily",
                "start_date": "20240101",  # 默认今年数据
                "end_date": "20241231"
            }
        elif interface == "stock_zh_a_spot_em":
            params = {}
        elif interface == "stock_yjbb_em":
            params = {"date": "2024"}
        
        # 根据时间范围调整参数
        if 'time_range' in context.entities:
            time_range = context.entities['time_range']
            if "最近" in time_range and "天" in time_range:
                days = re.search(r'(\d+)', time_range)
                if days:
                    from datetime import datetime, timedelta
                    end_date = datetime.now()
                    start_date = end_date - timedelta(days=int(days.group(1)))
                    params.update({
                        "start_date": start_date.strftime("%Y%m%d"),
                        "end_date": end_date.strftime("%Y%m%d")
                    })
        
        return params

    async def _analyze_data(self, context: AnalysisContext, data_responses: List[PaginatedDataResponse]) -> AnalysisResult:
        """分析数据并生成洞察"""
        insights = []
        data_points = {}
        charts_suggested = []

        if not data_responses:
            # 使用改进的降级策略
            return await self._generate_fallback_analysis(context)

        # 分析每个数据响应
        for response in data_responses:
            if response.data:
                df = pd.DataFrame(response.data)

                # 根据意图类型进行不同的分析
                if context.intent == IntentType.STOCK_ANALYSIS:
                    insights.extend(self._analyze_stock_data(df, data_points))
                    charts_suggested.extend(["价格走势图", "成交量图", "技术指标图"])

                elif context.intent == IntentType.MARKET_OVERVIEW:
                    insights.extend(self._analyze_market_data(df, data_points))
                    charts_suggested.extend(["市场热力图", "行业分布图", "涨跌分布图"])

                elif context.intent == IntentType.FINANCIAL_METRICS:
                    insights.extend(self._analyze_financial_data(df, data_points))
                    charts_suggested.extend(["财务指标雷达图", "同行对比图"])

        # 确保总是有洞察，即使没有实际数据
        if not insights:
            insights = self._generate_default_insights(context)

        # 如果洞察仍然不足，补充更多内容
        if len(insights) < 2:
            additional_insights = self._generate_additional_insights(context, data_points)
            insights.extend(additional_insights)

        # 生成分析摘要
        summary = self._generate_summary(context, insights, data_points)

        # 评估风险等级
        risk_level = self._assess_risk_level(context, data_points)

        return AnalysisResult(
            summary=summary,
            insights=insights,
            recommendations=[],  # 将在下一步生成
            data_points=data_points,
            charts_suggested=list(set(charts_suggested)),
            risk_level=risk_level,
            confidence=0.8
        )

    def _analyze_stock_data(self, df: pd.DataFrame, data_points: Dict[str, Any]) -> List[str]:
        """分析股票数据"""
        insights = []

        try:
            # 检查数据列
            if '收盘' in df.columns or 'close' in df.columns:
                close_col = '收盘' if '收盘' in df.columns else 'close'
                prices = df[close_col].astype(float)

                # 价格趋势分析
                if len(prices) > 1:
                    price_change = (prices.iloc[-1] - prices.iloc[0]) / prices.iloc[0] * 100
                    data_points['price_change_pct'] = round(price_change, 2)

                    if price_change > 5:
                        insights.append(f"股价呈现强劲上涨趋势，累计涨幅{price_change:.2f}%")
                    elif price_change > 0:
                        insights.append(f"股价温和上涨，累计涨幅{price_change:.2f}%")
                    elif price_change > -5:
                        insights.append(f"股价小幅下跌，累计跌幅{abs(price_change):.2f}%")
                    else:
                        insights.append(f"股价大幅下跌，累计跌幅{abs(price_change):.2f}%")

                # 波动率分析
                if len(prices) > 5:
                    volatility = prices.pct_change().std() * 100
                    data_points['volatility'] = round(volatility, 2)

                    if volatility > 3:
                        insights.append(f"股价波动较大，日均波动率{volatility:.2f}%")
                    elif volatility > 1.5:
                        insights.append(f"股价波动适中，日均波动率{volatility:.2f}%")
                    else:
                        insights.append(f"股价相对稳定，日均波动率{volatility:.2f}%")

            # 成交量分析
            if '成交量' in df.columns or 'volume' in df.columns:
                volume_col = '成交量' if '成交量' in df.columns else 'volume'
                volumes = df[volume_col].astype(float)

                if len(volumes) > 5:
                    avg_volume = volumes.mean()
                    recent_volume = volumes.iloc[-5:].mean()
                    volume_ratio = recent_volume / avg_volume

                    data_points['volume_ratio'] = round(volume_ratio, 2)

                    if volume_ratio > 1.5:
                        insights.append("近期成交量明显放大，市场关注度提升")
                    elif volume_ratio < 0.7:
                        insights.append("近期成交量萎缩，市场参与度下降")
                    else:
                        insights.append("成交量保持正常水平")

        except Exception as e:
            logger.warning(f"股票数据分析出错: {e}")
            insights.append("数据分析过程中出现异常")

        return insights

    def _analyze_market_data(self, df: pd.DataFrame, data_points: Dict[str, Any]) -> List[str]:
        """分析市场数据"""
        insights = []

        try:
            if '涨跌幅' in df.columns:
                change_pct = df['涨跌幅'].astype(float)

                # 涨跌分布
                rising_count = (change_pct > 0).sum()
                falling_count = (change_pct < 0).sum()
                total_count = len(change_pct)

                rising_ratio = rising_count / total_count * 100
                falling_ratio = falling_count / total_count * 100
                data_points['rising_ratio'] = round(rising_ratio, 1)
                data_points['falling_ratio'] = round(falling_ratio, 1)

                if rising_ratio > 70:
                    insights.append(f"市场情绪乐观，{rising_ratio:.1f}%的股票上涨")
                elif rising_ratio > 50:
                    insights.append(f"市场表现平衡，{rising_ratio:.1f}%的股票上涨")
                else:
                    insights.append(f"市场情绪偏弱，仅{rising_ratio:.1f}%的股票上涨")

                # 涨跌幅分布
                strong_rising = (change_pct > 5).sum()
                strong_falling = (change_pct < -5).sum()

                if strong_rising > total_count * 0.1:
                    insights.append(f"有{strong_rising}只股票涨幅超过5%，市场活跃度较高")

                if strong_falling > total_count * 0.1:
                    insights.append(f"有{strong_falling}只股票跌幅超过5%，需注意风险")

        except Exception as e:
            logger.warning(f"市场数据分析出错: {e}")
            insights.append("市场数据分析过程中出现异常")

        return insights

    def _analyze_financial_data(self, df: pd.DataFrame, data_points: Dict[str, Any]) -> List[str]:
        """分析财务数据"""
        insights = []

        try:
            # 分析PE、PB等估值指标
            if 'PE' in df.columns or '市盈率' in df.columns:
                pe_col = 'PE' if 'PE' in df.columns else '市盈率'
                pe_values = pd.to_numeric(df[pe_col], errors='coerce').dropna()

                if not pe_values.empty:
                    avg_pe = pe_values.mean()
                    data_points['avg_pe'] = round(avg_pe, 2)

                    if avg_pe > 30:
                        insights.append(f"平均市盈率{avg_pe:.1f}倍，估值偏高")
                    elif avg_pe > 15:
                        insights.append(f"平均市盈率{avg_pe:.1f}倍，估值合理")
                    else:
                        insights.append(f"平均市盈率{avg_pe:.1f}倍，估值偏低")

            # 分析ROE等盈利指标
            if 'ROE' in df.columns or '净资产收益率' in df.columns:
                roe_col = 'ROE' if 'ROE' in df.columns else '净资产收益率'
                roe_values = pd.to_numeric(df[roe_col], errors='coerce').dropna()

                if not roe_values.empty:
                    avg_roe = roe_values.mean()
                    data_points['avg_roe'] = round(avg_roe, 2)

                    if avg_roe > 15:
                        insights.append(f"净资产收益率{avg_roe:.1f}%，盈利能力强")
                    elif avg_roe > 10:
                        insights.append(f"净资产收益率{avg_roe:.1f}%，盈利能力良好")
                    else:
                        insights.append(f"净资产收益率{avg_roe:.1f}%，盈利能力一般")

        except Exception as e:
            logger.warning(f"财务数据分析出错: {e}")
            insights.append("财务数据分析过程中出现异常")

        return insights

    def _generate_summary(self, context: AnalysisContext, insights: List[str], data_points: Dict[str, Any]) -> str:
        """生成分析摘要"""
        if context.intent == IntentType.STOCK_ANALYSIS:
            stock_codes = context.entities.get('stock_codes', ['目标股票'])
            stock_name = stock_codes[0] if stock_codes else "目标股票"

            if 'price_change_pct' in data_points:
                change = data_points['price_change_pct']
                trend = "上涨" if change > 0 else "下跌"
                return f"{stock_name}近期呈现{trend}趋势，累计变动{abs(change):.2f}%。" + \
                       f"基于技术分析，该股票{'表现强劲' if change > 5 else '表现平稳' if change > -5 else '承压明显'}。"
            else:
                return f"对{stock_name}的分析显示，需要更多数据来做出准确判断。"

        elif context.intent == IntentType.MARKET_OVERVIEW:
            if 'rising_ratio' in data_points:
                ratio = data_points['rising_ratio']
                sentiment = "乐观" if ratio > 60 else "谨慎" if ratio > 40 else "悲观"
                return f"当前市场整体情绪{sentiment}，{ratio:.1f}%的股票实现上涨。" + \
                       f"市场{'活跃度较高' if ratio > 60 else '表现平衡' if ratio > 40 else '承压明显'}。"
            else:
                return "市场整体分析显示，当前处于震荡调整阶段。"

        elif context.intent == IntentType.FINANCIAL_METRICS:
            return "财务指标分析显示，" + "，".join(insights[:2]) if insights else "财务数据分析完成。"

        else:
            return "基于当前数据的分析已完成，" + "，".join(insights[:2]) if insights else "分析结果有限。"

    def _assess_risk_level(self, context: AnalysisContext, data_points: Dict[str, Any]) -> str:
        """评估风险等级"""
        risk_score = 0

        # 根据上下文调整风险评估
        if context and context.intent == IntentType.STOCK_ANALYSIS:
            # 股票分析的风险评估更严格
            risk_score += 1

        # 基于波动率评估风险
        if 'volatility' in data_points:
            volatility = data_points['volatility']
            if volatility > 3:
                risk_score += 3
            elif volatility > 1.5:
                risk_score += 2
            else:
                risk_score += 1

        # 基于价格变动评估风险
        if 'price_change_pct' in data_points:
            change = abs(data_points['price_change_pct'])
            if change > 10:
                risk_score += 3
            elif change > 5:
                risk_score += 2
            else:
                risk_score += 1

        # 基于市场情绪评估风险
        if 'rising_ratio' in data_points:
            ratio = data_points['rising_ratio']
            if ratio < 30 or ratio > 80:
                risk_score += 2
            else:
                risk_score += 1

        # 转换为风险等级
        if risk_score >= 7:
            return "高风险"
        elif risk_score >= 4:
            return "中等风险"
        else:
            return "低风险"

    def _generate_recommendations(self, context: AnalysisContext, analysis_result: AnalysisResult) -> AnalysisResult:
        """生成投资建议"""
        recommendations = []

        # 基于意图类型生成建议
        if context.intent == IntentType.STOCK_ANALYSIS:
            recommendations.extend(self._generate_stock_recommendations(analysis_result))

        elif context.intent == IntentType.MARKET_OVERVIEW:
            recommendations.extend(self._generate_market_recommendations(analysis_result))

        elif context.intent == IntentType.FINANCIAL_METRICS:
            recommendations.extend(self._generate_financial_recommendations(analysis_result))

        else:
            recommendations.extend(self._generate_general_recommendations(analysis_result))

        # 基于风险等级添加风险提示
        if analysis_result.risk_level == "高风险":
            recommendations.append("⚠️ 当前风险等级较高，建议谨慎投资，做好风险控制")
        elif analysis_result.risk_level == "中等风险":
            recommendations.append("⚡ 当前存在一定风险，建议适度配置，分散投资")
        else:
            recommendations.append("✅ 当前风险相对较低，可考虑适当配置")

        analysis_result.recommendations = recommendations
        return analysis_result

    def _generate_stock_recommendations(self, analysis_result: AnalysisResult) -> List[str]:
        """生成股票投资建议"""
        recommendations = []
        data_points = analysis_result.data_points

        if 'price_change_pct' in data_points:
            change = data_points['price_change_pct']

            if change > 10:
                recommendations.append("📈 股价涨幅较大，建议关注回调风险，可考虑分批减仓")
            elif change > 5:
                recommendations.append("📊 股价表现良好，可继续持有，注意设置止盈点")
            elif change > 0:
                recommendations.append("📉 股价温和上涨，可适当加仓，但需控制仓位")
            elif change > -5:
                recommendations.append("🔍 股价小幅下跌，可关注支撑位，寻找买入机会")
            else:
                recommendations.append("⚠️ 股价跌幅较大，建议等待企稳信号再考虑介入")

        if 'volatility' in data_points:
            volatility = data_points['volatility']
            if volatility > 3:
                recommendations.append("🎢 波动率较高，建议采用分批建仓策略，降低风险")

        if 'volume_ratio' in data_points:
            volume_ratio = data_points['volume_ratio']
            if volume_ratio > 1.5:
                recommendations.append("📊 成交量放大，关注资金流向，可能有重要消息")
            elif volume_ratio < 0.7:
                recommendations.append("📉 成交量萎缩，市场关注度不高，需谨慎操作")

        return recommendations

    def _generate_market_recommendations(self, analysis_result: AnalysisResult) -> List[str]:
        """生成市场投资建议"""
        recommendations = []
        data_points = analysis_result.data_points

        if 'rising_ratio' in data_points:
            ratio = data_points['rising_ratio']

            if ratio > 70:
                recommendations.append("🚀 市场情绪乐观，可适当增加仓位，但需防范过热风险")
            elif ratio > 50:
                recommendations.append("⚖️ 市场表现均衡，建议保持现有配置，观察后续走势")
            else:
                recommendations.append("🛡️ 市场情绪偏弱，建议降低仓位，等待更好时机")

        recommendations.append("🔄 建议关注行业轮动机会，分散投资降低风险")
        recommendations.append("📅 定期关注宏观经济数据和政策变化")

        return recommendations

    def _generate_financial_recommendations(self, analysis_result: AnalysisResult) -> List[str]:
        """生成财务分析建议"""
        recommendations = []
        data_points = analysis_result.data_points

        if 'avg_pe' in data_points:
            pe = data_points['avg_pe']
            if pe > 30:
                recommendations.append("📊 估值偏高，建议等待回调或寻找低估值标的")
            elif pe < 15:
                recommendations.append("💎 估值相对较低，可关注基本面改善的投资机会")

        if 'avg_roe' in data_points:
            roe = data_points['avg_roe']
            if roe > 15:
                recommendations.append("⭐ 盈利能力强，可重点关注此类优质标的")
            elif roe < 10:
                recommendations.append("⚠️ 盈利能力一般，需结合其他指标综合判断")

        recommendations.append("📈 建议关注财务指标的趋势变化，而非单一时点数据")

        return recommendations

    def _generate_general_recommendations(self, analysis_result: AnalysisResult) -> List[str]:
        """生成通用建议"""
        recommendations = [
            "📊 建议结合多个维度的数据进行综合分析",
            "⏰ 保持长期投资视角，避免短期情绪化操作",
            "🎯 根据个人风险承受能力制定投资策略",
            "📚 持续学习和关注市场动态"
        ]

        # 根据分析结果调整建议
        if analysis_result.confidence > 0.8:
            recommendations.append("✅ 分析结果置信度较高，可作为参考")
        elif analysis_result.confidence < 0.5:
            recommendations.append("⚠️ 分析结果置信度较低，建议谨慎参考")

        return recommendations

    def _generate_default_insights(self, context: AnalysisContext) -> List[str]:
        """生成默认洞察，确保总是有内容"""
        insights = []

        if context.intent == IntentType.STOCK_ANALYSIS:
            stock_codes = context.entities.get('stock_codes', [])
            if stock_codes:
                stock_code = stock_codes[0]
                insights.extend([
                    f"已识别股票代码: {stock_code}",
                    f"股票{stock_code}属于A股市场，建议关注其基本面表现",
                    "当前市场环境下，建议重点关注公司的盈利能力和成长性",
                    "技术面分析需要结合更多历史数据进行综合判断"
                ])
            else:
                insights.extend([
                    "股票分析需要明确的标的代码",
                    "建议提供具体的股票代码以获得更准确的分析",
                    "A股市场有4000+只股票，精准分析需要具体标的"
                ])

        elif context.intent == IntentType.MARKET_OVERVIEW:
            insights.extend([
                "A股市场整体呈现结构性分化特征",
                "当前宏观环境对市场情绪有重要影响",
                "建议关注政策导向和资金流向变化",
                "优质蓝筹股和成长股仍具备长期配置价值"
            ])

        elif context.intent == IntentType.FINANCIAL_METRICS:
            insights.extend([
                "财务指标是评估公司价值的重要工具",
                "PE、PB、ROE等指标需要结合行业平均水平分析",
                "财务数据的趋势比单一时点数据更有参考价值",
                "建议结合现金流量表进行综合分析"
            ])

        elif context.intent == IntentType.COMPARISON_ANALYSIS:
            insights.extend([
                "股票对比分析需要从多个维度进行评估",
                "建议从基本面、技术面、估值面进行综合对比",
                "同行业对比更具参考价值",
                "风险收益比是选择的重要考量因素"
            ])

        elif context.intent == IntentType.INVESTMENT_ADVICE:
            insights.extend([
                "投资建议需要结合个人风险偏好制定",
                "分散投资是降低风险的有效策略",
                "长期投资通常比短期投机更稳健",
                "建议定期评估和调整投资组合"
            ])

        elif context.intent == IntentType.RISK_ASSESSMENT:
            insights.extend([
                "投资风险来源于多个方面：市场风险、行业风险、个股风险",
                "风险评估需要考虑投资者的风险承受能力",
                "适当的风险管理措施可以有效控制损失",
                "建议设置止损点和目标收益点"
            ])

        else:
            insights.extend([
                "金融市场分析需要综合考虑多种因素",
                "建议关注宏观经济、行业趋势和公司基本面",
                "理性投资，避免情绪化决策"
            ])

        return insights[:4]  # 限制数量，避免过多

    def _generate_additional_insights(self, context: AnalysisContext, data_points: Dict[str, Any]) -> List[str]:
        """生成额外的洞察补充"""
        additional = []

        # 基于数据点生成洞察
        if data_points:
            if 'price_change_pct' in data_points:
                change = data_points['price_change_pct']
                if change > 5:
                    additional.append(f"价格涨幅{change:.1f}%，表现较为强势")
                elif change < -5:
                    additional.append(f"价格跌幅{change:.1f}%，需要关注风险")
                else:
                    additional.append("价格波动相对温和，走势较为稳定")

            if 'volatility' in data_points:
                vol = data_points['volatility']
                if vol > 3:
                    additional.append("波动率较高，适合风险偏好较强的投资者")
                else:
                    additional.append("波动率适中，风险相对可控")

        # 基于意图生成通用洞察
        if context.intent == IntentType.STOCK_ANALYSIS:
            additional.extend([
                "建议关注公司的核心竞争力和护城河",
                "行业地位和市场份额是重要考量因素"
            ])
        elif context.intent == IntentType.MARKET_OVERVIEW:
            additional.extend([
                "市场情绪和资金流向值得密切关注",
                "国际市场动态对A股也有重要影响"
            ])

        return additional[:2]  # 限制补充数量

    async def _generate_fallback_analysis(self, context: AnalysisContext) -> AnalysisResult:
        """生成降级分析结果，当数据获取失败时使用"""
        # 生成基础洞察
        insights = self._generate_default_insights(context)

        # 生成基础建议
        recommendations = self._generate_fallback_recommendations(context)

        # 生成摘要
        summary = self._generate_fallback_summary(context)

        # 设置数据点
        data_points = {
            "analysis_mode": "fallback",
            "data_availability": "limited",
            "confidence_level": "基础分析"
        }

        # 建议图表
        charts_suggested = self._get_suggested_charts(context)

        # 评估风险等级
        risk_level = self._get_fallback_risk_level(context)

        # 设置置信度
        confidence = self._calculate_fallback_confidence(context)

        return AnalysisResult(
            summary=summary,
            insights=insights,
            recommendations=recommendations,
            data_points=data_points,
            charts_suggested=charts_suggested,
            risk_level=risk_level,
            confidence=confidence
        )

    def _generate_fallback_recommendations(self, context: AnalysisContext) -> List[str]:
        """生成降级模式下的建议"""
        recommendations = []

        if context.intent == IntentType.STOCK_ANALYSIS:
            stock_codes = context.entities.get('stock_codes', [])
            if stock_codes:
                stock_code = stock_codes[0]
                recommendations.extend([
                    f"建议通过多个渠道获取{stock_code}的最新数据",
                    "关注公司基本面信息：财务报表、行业地位、竞争优势",
                    "技术面分析：关注价格趋势、成交量变化、技术指标",
                    "风险控制：设置合理的止损点，控制仓位大小"
                ])
            else:
                recommendations.extend([
                    "请提供具体的股票代码以获得更精准的分析",
                    "建议关注优质蓝筹股和成长股",
                    "分散投资，降低单一股票风险"
                ])

        elif context.intent == IntentType.MARKET_OVERVIEW:
            recommendations.extend([
                "关注主要指数走势：上证指数、深证成指、创业板指",
                "观察市场情绪指标：成交量、涨跌比例、资金流向",
                "关注政策面变化和宏观经济数据",
                "保持理性投资心态，避免追涨杀跌"
            ])

        elif context.intent == IntentType.FINANCIAL_METRICS:
            recommendations.extend([
                "重点关注PE、PB、ROE、ROA等核心财务指标",
                "对比同行业平均水平进行相对估值",
                "关注财务数据的趋势变化，而非单一时点数据",
                "结合现金流量表分析公司的真实盈利质量"
            ])

        elif context.intent == IntentType.INVESTMENT_ADVICE:
            recommendations.extend([
                "制定明确的投资目标和风险承受能力评估",
                "采用分散投资策略，不要把鸡蛋放在一个篮子里",
                "长期投资通常比短期投机更稳健",
                "定期评估和调整投资组合"
            ])

        else:
            recommendations.extend([
                "建议进一步明确分析需求",
                "关注市场基本面和技术面的综合分析",
                "保持理性投资心态"
            ])

        return recommendations[:4]  # 限制数量

    def _generate_fallback_summary(self, context: AnalysisContext) -> str:
        """生成降级模式下的摘要"""
        if context.intent == IntentType.STOCK_ANALYSIS:
            stock_codes = context.entities.get('stock_codes', [])
            if stock_codes:
                return f"正在分析股票{stock_codes[0]}，当前基于基础分析框架提供投资参考"
            else:
                return "股票分析需要明确的标的代码，建议提供具体股票代码"

        elif context.intent == IntentType.MARKET_OVERVIEW:
            return "A股市场整体分析：建议关注主要指数走势和市场情绪变化"

        elif context.intent == IntentType.FINANCIAL_METRICS:
            return "财务指标分析：重点关注估值指标和盈利能力指标"

        elif context.intent == IntentType.COMPARISON_ANALYSIS:
            return "对比分析：建议从基本面、技术面、估值面进行多维度比较"

        elif context.intent == IntentType.INVESTMENT_ADVICE:
            return "投资建议：基于风险收益平衡原则，提供个性化投资策略"

        elif context.intent == IntentType.RISK_ASSESSMENT:
            return "风险评估：全面分析投资风险，制定相应的风险管理策略"

        else:
            return "基于当前信息提供基础分析，建议获取更多数据以提升分析精度"

    def _get_suggested_charts(self, context: AnalysisContext) -> List[str]:
        """获取建议的图表类型"""
        if context.intent == IntentType.STOCK_ANALYSIS:
            return ["K线图", "成交量图", "技术指标图", "财务指标图"]
        elif context.intent == IntentType.MARKET_OVERVIEW:
            return ["市场热力图", "行业分布图", "涨跌分布图", "资金流向图"]
        elif context.intent == IntentType.FINANCIAL_METRICS:
            return ["财务指标雷达图", "同行对比图", "趋势分析图"]
        elif context.intent == IntentType.COMPARISON_ANALYSIS:
            return ["对比分析图", "相关性分析图", "风险收益散点图"]
        else:
            return ["综合分析图", "趋势图"]

    def _get_fallback_risk_level(self, context: AnalysisContext) -> str:
        """获取降级模式下的风险等级"""
        if context.intent == IntentType.STOCK_ANALYSIS:
            return "中等风险"
        elif context.intent == IntentType.MARKET_OVERVIEW:
            return "中等风险"
        elif context.intent == IntentType.INVESTMENT_ADVICE:
            return "风险等级待评估"
        else:
            return "中等风险"

    def _calculate_fallback_confidence(self, context: AnalysisContext) -> float:
        """计算降级模式下的置信度"""
        base_confidence = 0.6

        # 根据实体识别质量调整
        if context.entities and len(context.entities) > 0:
            base_confidence += 0.1

        # 根据意图识别置信度调整
        if context.confidence > 0.8:
            base_confidence += 0.1
        elif context.confidence < 0.5:
            base_confidence -= 0.1

        return min(max(base_confidence, 0.3), 0.8)  # 限制在0.3-0.8之间

# 创建全局实例
# 优先使用LLM模式，如果不可用则回退到规则模式
llm_analysis_handler = LLMAnalysisHandler(use_llm=True)

# 创建仅使用规则的实例（用于对比测试）
rule_based_handler = LLMAnalysisHandler(use_llm=False)
