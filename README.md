# MCP 统一服务 - AkShare数据 + 量化回测 v2.2.0

一个统一的MCP (Microservice Control Protocol) 服务，提供两大核心功能：
1. **AkShare数据接口** - 通过标准化MCP协议访问中国金融市场数据
2. **量化回测服务** - 基于Backtrader的策略回测和性能分析

## 🚀 核心功能

### 📊 AkShare数据接口 (MCP协议)
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

### 1. MCP数据接口
```bash
POST /api/mcp
```

**请求示例**:
```bash
# 获取股票历史数据
curl -X POST http://localhost:12001/api/mcp \
-H "Content-Type: application/json" \
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

# 获取基金信息
curl -X POST http://localhost:12001/api/mcp \
-H "Content-Type: application/json" \
-d '{
    "interface": "fund_em_open_fund_info",
    "params": {"fund": "000001", "indicator": "单位净值走势"},
    "request_id": "test002"
}'
```

### 2. 回测接口
```bash
POST /api/backtest
```

支持文件上传和AkShare数据源两种方式。

### 3. 代码回测接口
```bash
POST /api/backtest-code
```

只需提供策略代码，数据直接从AkShare获取。

**请求示例**:
```bash
curl -X POST http://localhost:12001/api/backtest-code \
-H "Content-Type: application/json" \
-d '{
    "strategy_code": "import backtrader as bt\n\nclass MyStrategy(bt.Strategy):\n    def __init__(self):\n        self.sma = bt.indicators.SimpleMovingAverage(self.data.close, period=20)\n\n    def next(self):\n        if self.data.close[0] > self.sma[0]:\n            self.buy()\n        elif self.data.close[0] < self.sma[0]:\n            self.sell()\n",
    "symbol": "000001",
    "start_date": "2023-01-01",
    "end_date": "2023-12-31",
    "params": {"cash": 100000},
    "benchmark_symbol": "000300"
}'
```

### 4. AkShare代码执行接口
```bash
POST /api/execute-akshare
```

直接提交AkShare代码片段，执行并返回结果。支持多种输出格式：JSON、CSV和HTML。

**请求示例**:
```bash
curl -X POST http://localhost:12001/api/execute-akshare \
-H "Content-Type: application/json" \
-d '{
    "code": "import akshare as ak\nstock_sz_a_spot_em_df = ak.stock_sz_a_spot_em()\nstock_sz_a_spot_em_df",
    "format": "json"
}'
```

**响应示例**:
```json
{
  "result": [
    {
      "序号": 1,
      "代码": "000001",
      "名称": "平安银行",
      "最新价": 8.12,
      "涨跌幅": 0.87,
      "涨跌额": 0.07,
      "成交量": 31218700,
      "成交额": 252274920.0,
      "振幅": 1.24,
      "最高": 8.19,
      "最低": 8.09,
      "今开": 8.12,
      "昨收": 8.05,
      "量比": 0.79,
      "换手率": 0.16,
      "市盈率-动态": 4.65,
      "市净率": 0.69,
      "总市值": 157553376000.0,
      "流通市值": 157553376000.0,
      "涨速": 0.0,
      "5分钟涨跌": 0.0,
      "60日涨跌幅": -9.78,
      "年初至今涨跌幅": -5.36
    },
    ...
  ],
  "format": "json",
  "error": null
}
```

### 5. 数据源接口
```bash
GET /api/data-sources
```

获取可用的AkShare数据源列表。

## 🖥️ Web界面功能

### 四个主要标签页：

1. **File Upload** - 上传策略和数据文件进行回测
2. **AkShare Data** - 使用AkShare数据源进行回测
3. **MCP Interface** - 测试MCP数据接口
4. **Integrated Backtest** - 直接使用AkShare数据接口进行回测，无需手动下载数据

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
├── api/                  # API路由
├── core/                 # 核心功能
├── models/               # 数据模型
├── static/               # Web界面
├── tests/                # 测试和示例
├── utils/                # 工具函数
├── adaptors/             # MCP适配器
├── main.py               # 服务入口
└── requirements.txt      # 依赖包
```

### 示例策略
- `tests/sample_strategies/simple_ma_strategy.py` - 简单双均线策略
- `tests/sample_strategies/rsi_strategy.py` - RSI超买超卖策略

#### 简单双均线策略示例
```python
import backtrader as bt

class SimpleMAStrategy(bt.Strategy):
    params = (
        ('fast_period', 10),  # 快速均线周期
        ('slow_period', 30),  # 慢速均线周期
    )
    
    def __init__(self):
        # 添加移动平均线指标
        self.fast_ma = bt.indicators.SMA(self.datas[0], period=self.params.fast_period)
        self.slow_ma = bt.indicators.SMA(self.datas[0], period=self.params.slow_period)
        self.crossover = bt.indicators.CrossOver(self.fast_ma, self.slow_ma)
        
    def next(self):
        if not self.position:  # 没有持仓
            if self.crossover > 0:  # 快线上穿慢线
                self.buy()  # 买入
        else:  # 已有持仓
            if self.crossover < 0:  # 快线下穿慢线
                self.sell()  # 卖出
```

## 📝 更新日志

### v2.2.0 (最新)
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
