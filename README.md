# MCP 统一服务 - AkShare数据 + 量化回测 v3.0.0

一个统一的MCP (Microservice Control Protocol) 服务，提供两大核心功能：
1. **AkShare数据接口** - 通过标准化MCP协议访问中国金融市场数据
2. **量化回测服务** - 基于Backtrader的策略回测和性能分析

## 🚀 核心功能

### 📊 AkShare数据接口 (MCP协议)
- **用户认证 (OAuth2/JWT)**: 通过Token保护核心API接口，确保服务安全。
- **数据缓存**: 内置文件缓存机制，显著提升常用数据的响应速度。
- 股票历史数据 (`stock_zh_a_hist`)
- 基金信息 (`fund_em_open_fund_info`) 
- 指数历史数据 (`index_zh_a_hist`)
- 股票实时数据 (`stock_zh_a_spot_em`)
- ETF实时数据 (`fund_etf_spot_em`)

### 🎯 量化回测服务
- 策略文件上传和执行
- AkShare数据源集成
- 综合性能指标分析
- 基准比较和风险评估
- 可视化图表生成

## 🌐 服务访问

### 在线服务
- **Web界面**: https://work-2-pwhlzzlajkygnknl.prod-runtime.all-hands.dev
- **API文档**: https://work-2-pwhlzzlajkygnknl.prod-runtime.all-hands.dev/docs

### 本地部署
```bash
# 启动服务
python main.py

# 访问地址
- Web界面: http://localhost:12001
- API文档: http://localhost:12001/docs
```

## 📖 API接口

所有API端点都以 `/api` 为前缀。

### 1. 认证接口
```bash
# 获取Token
POST /api/token

# 获取当前用户信息 (需要Token)
GET /api/users/me
```

### 2. MCP数据接口 (需要Token)
```bash
POST /api/mcp-data
```

**请求示例**:
```bash
# 获取股票历史数据
curl -X POST http://localhost:12001/api/mcp-data 
-H "Content-Type: application/json" 
-H "Authorization: Bearer <YOUR_TOKEN>" 
-d '{
    "interface": "stock_zh_a_hist",
    "params": {
        "symbol": "000001", 
        "period": "daily",
        "start_date": "20241201",
        "end_date": "20241210"
    },
    "request_id": "test001"
}'
```

### 3. 回测接口 (需要Token)
```bash
POST /api/backtest
```

### 4. 代码回测接口 (需要Token)
```bash
POST /api/backtest-code
```

### 5. AkShare代码执行接口 (需要Token)
```bash
POST /api/execute-akshare
```

### 6. 数据源接口
```bash
GET /api/data-sources
```

获取可用的AkShare数据源列表。

## 🖥️ Web界面功能

一个功能完善的单页应用，提供以下功能：

1. **用户认证** - 提供登录界面，管理访问权限。
2. **回测** - 支持多种回测方式：
    - 上传策略和数据文件。
    - 直接使用AkShare数据源进行回测。
3. **MCP接口测试** - 提供UI界面方便地测试MCP数据接口。
4. **结果展示** - 以图表和表格形式清晰地展示回测性能和数据。

## 🛠️ 安装和部署

### 环境要求
- Python 3.9+
- 依赖包见 `requirements.txt`

### 安装步骤
```bash
# 1. 克隆仓库
git clone https://github.com/sys3222/akshare-mcp-adapter.git
cd akshare-mcp-adapter

# 2. 安装依赖
pip install -r requirements.txt

# 3. 启动服务
python main.py
```

### Docker部署
```bash
# 构建镜像
docker build -t mcp-unified-service .

# 运行容器
docker run -p 12001:12001 mcp-unified-service
```

## 📊 支持的数据源

### AkShare ETF数据
- 黄金ETF (518880)
- 纳指100 (513100)
- 创业板100 (159915)
- 上证180 (510180)
- 沪深300ETF (510300)

### AkShare指数数据
- 上证指数 (000001)
- 沪深300 (000300)
- 中证500 (000905)
- 深证成指 (399001)
- 创业板指 (399006)

## 📈 回测指标

### 收益指标
- 总收益率 (Total Return)
- 年化收益率 (Annual Return)
- 月度收益率 (Monthly Returns)

### 风险指标
- 夏普比率 (Sharpe Ratio)
- 索提诺比率 (Sortino Ratio)
- 最大回撤 (Max Drawdown)

### 交易统计
- 总交易次数 (Total Trades)
- 胜率 (Win Rate)
- 盈利因子 (Profit Factor)

### 基准比较
- Alpha系数
- Beta系数
- 信息比率 (Information Ratio)

## 🔧 开发和测试

### 项目结构
```
├── api/                  # API路由 (FastAPI)
├── handlers/             # 业务逻辑处理器
├── core/                 # 核心功能 (回测引擎、MCP协议)
├── models/               # 数据模型 (Pydantic)
├── static/               # Web界面 (HTML/JS/CSS)
├── tests/                # 单元测试和集成测试
│   ├── unit/             # 单元测试
│   └── sample_strategies/ # 示例策略
├── utils/                # 工具函数
├── adaptors/             # 数据源适配器 (AkShare)
├── main.py               # 服务入口
└── requirements.txt      # 依赖包
```

### 运行测试
项目包含一套完整的单元测试和集成测试，使用 `pytest` 框架。

```bash
# 1. 安装测试依赖
pip install pytest pytest-asyncio

# 2. 运行测试
pytest tests/
```

### 示例策略
- `tests/sample_strategies/simple_ma_strategy.py` - 简单双均线策略
- `tests/sample_strategies/rsi_strategy.py` - RSI超买超卖策略

## 📝 更新日志

### v3.0.0 (最新)
- ✨ **新增 认证与授权**: 引入OAuth2/JWT保护核心API，提升服务安全性。
- ✨ **新增 数据缓存机制**: 为AkShare接口增加文件缓存，大幅提升重复数据请求的响应速度。
- ✨ **重构 Web用户界面**: `index.html` 全面升级为单页应用，支持用户登录、多种回测模式和交互式结果展示。
- ✨ **优化 API数据格式**: 对MCP返回的数据进行统一规范化处理，确保输出格式的一致性。
- ✨ **新增 单元测试**: 增加了对核心功能的单元测试。

### v2.2.0
- ✅ 新增AkShare代码执行接口，支持直接提交代码片段获取数据
- ✅ 新增代码回测接口，只需提供策略代码即可使用AkShare数据进行回测
- ✅ 添加示例策略文件，包括双均线策略和RSI策略
- ✅ 优化数据处理逻辑，支持更多数据格式输出（JSON、CSV、HTML）

### v2.1.0
- ✅ 完全集成AkShare数据接口和回测功能
- ✅ 新增"集成回测"标签页，直接使用AkShare数据进行回测
- ✅ 优化数据缓存机制，提高回测速度
- ✅ 支持股票、ETF和指数数据的统一访问

### v2.0.0
- ✅ 集成MCP协议端点
- ✅ 统一AkShare数据访问和回测功能
- ✅ 新增Web界面MCP测试标签页
- ✅ 完善API文档和示例

### v1.0.0
- ✅ 基础回测服务
- ✅ AkShare数据源集成
- ✅ Web界面和API

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## 🤝 贡献

欢迎提交Issue和Pull Request来改进这个项目！

---

**GitHub仓库**: https://github.com/sys3222/akshare-mcp-adapter
