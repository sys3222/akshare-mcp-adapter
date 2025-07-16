# AkShare MCP Adapter - 产品文档

## 📋 **产品概述**

AkShare MCP Adapter 是一个基于 FastAPI 的金融数据分析平台，集成了 LLM 智能分析功能，提供统一的 MCP (Model Context Protocol) 接口来访问 AkShare 金融数据。

### **核心特性**

- 🧠 **智能LLM分析**：集成 Google Gemini 模型，支持自然语言查询
- 📊 **双模式分析**：LLM智能模式 + 规则快速模式
- 🔒 **安全认证**：JWT令牌认证，用户权限管理
- 💬 **现代化界面**：实时聊天式交互界面
- 🧪 **完整测试**：单元测试、集成测试、API测试
- 📈 **性能监控**：实时系统监控和指标收集
- 🔧 **配置管理**：统一的配置管理系统

## 🏗️ **系统架构**

### **技术栈**
- **后端框架**: FastAPI + Uvicorn
- **数据库**: SQLite (可扩展到 PostgreSQL)
- **LLM模型**: Google Gemini 1.5 Pro
- **数据源**: AkShare 金融数据接口
- **前端**: HTML5 + JavaScript + CSS3
- **测试框架**: pytest + unittest.mock
- **监控**: psutil + 自定义监控系统

### **模块结构**
```
akshare-mcp-adapter/
├── api/                    # API路由和端点
├── core/                   # 核心功能模块
│   ├── config.py          # 配置管理
│   ├── database.py        # 数据库操作
│   ├── mcp_protocol.py    # MCP协议实现
│   ├── monitoring.py      # 性能监控
│   └── security.py        # 安全认证
├── handlers/               # 业务逻辑处理器
│   ├── llm_handler.py     # LLM智能分析
│   ├── mcp_handler.py     # MCP数据处理
│   └── akshare_handler.py # AkShare接口
├── models/                 # 数据模型
├── static/                 # 静态文件
├── tests/                  # 测试套件
└── utils/                  # 工具函数
```

## 🚀 **快速开始**

### **1. 环境准备**

```bash
# 克隆项目
git clone https://github.com/sys3222/akshare-mcp-adapter.git
cd akshare-mcp-adapter

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
export GEMINI_API_KEY="your-gemini-api-key"
export SECRET_KEY="your-secret-key"
```

### **2. 启动服务**

```bash
# 开发模式
python main.py

# 或使用 uvicorn
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### **3. 访问界面**

- **Web界面**: http://localhost:8000/static/index.html
- **API文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/health

## 💡 **核心功能**

### **1. LLM智能分析**

#### **功能特性**
- **自然语言查询**: 支持中文自然语言输入
- **智能意图识别**: 自动识别股票分析、市场概览等意图
- **实体提取**: 自动提取股票代码、时间范围等关键信息
- **Function Calling**: 自动调用相应的数据接口
- **结构化输出**: 提供摘要、洞察、建议、风险评估

#### **使用示例**
```python
# API调用示例
import requests

response = requests.post(
    "http://localhost:8000/api/llm/analyze",
    headers={"Authorization": "Bearer your-token"},
    json={"query": "分析000001平安银行最近的表现"}
)

result = response.json()
print(f"分析摘要: {result['summary']}")
print(f"投资建议: {result['recommendations']}")
print(f"风险等级: {result['risk_level']}")
```

### **2. 双模式分析**

#### **LLM智能模式**
- 使用 Google Gemini 模型
- 支持复杂的自然语言理解
- 提供深度分析和个性化建议
- 适合复杂查询和决策支持

#### **规则快速模式**
- 基于预定义规则和模板
- 响应速度快，资源消耗低
- 适合标准化查询和批量处理
- 作为 LLM 模式的回退方案

### **3. 数据接口**

#### **支持的数据类型**
- **股票数据**: 实时行情、历史数据、财务指标
- **市场数据**: 指数数据、板块数据、资金流向
- **宏观数据**: 经济指标、政策信息
- **新闻数据**: 财经新闻、公告信息

#### **MCP协议支持**
```json
{
  "method": "get_data",
  "params": {
    "interface": "stock_zh_a_hist",
    "symbol": "000001",
    "period": "daily",
    "start_date": "20240101",
    "end_date": "20241231"
  }
}
```

## 🔧 **配置管理**

### **配置文件结构**
```json
{
  "environment": "production",
  "llm": {
    "provider": "gemini",
    "model_name": "gemini-1.5-pro-latest",
    "api_key": "your-api-key",
    "temperature": 0.7,
    "max_tokens": 4096
  },
  "database": {
    "url": "sqlite:///./akshare_mcp.db",
    "echo": false
  },
  "api": {
    "host": "0.0.0.0",
    "port": 8000,
    "cors_origins": ["*"]
  }
}
```

### **环境变量**
- `GEMINI_API_KEY`: Google Gemini API密钥
- `SECRET_KEY`: JWT签名密钥
- `DATABASE_URL`: 数据库连接URL
- `ENVIRONMENT`: 运行环境 (development/production/testing)

## 🧪 **测试体系**

### **测试类型**

#### **1. 单元测试**
```bash
# 运行单元测试
python -m pytest tests/unit/ -v --cov=handlers --cov=core
```

#### **2. 集成测试**
```bash
# 运行集成测试
python -m pytest tests/integration/ -v
```

#### **3. API测试**
```bash
# 运行API测试
python -m pytest tests/unit/test_api_llm.py -v
```

#### **4. 完整测试套件**
```bash
# 运行完整测试
bash run_llm_tests.sh
```

### **测试覆盖率**
- **目标覆盖率**: 80%+
- **核心模块**: handlers/, core/
- **测试报告**: 自动生成HTML报告

## 📊 **性能监控**

### **监控指标**
- **系统指标**: CPU、内存、磁盘使用率
- **API指标**: 响应时间、请求量、错误率
- **业务指标**: LLM调用次数、分析成功率

### **健康检查**
```bash
# 检查系统健康状态
curl http://localhost:8000/health

# 获取监控指标
curl http://localhost:8000/api/monitoring/metrics
```

### **性能基准**
- **API响应时间**: < 2秒 (95%分位)
- **LLM分析时间**: < 10秒
- **并发支持**: 100+ 并发用户
- **系统可用性**: 99.9%+

## 🔒 **安全特性**

### **认证授权**
- **JWT令牌**: 基于JWT的无状态认证
- **用户管理**: 用户注册、登录、权限控制
- **令牌过期**: 自动令牌刷新机制

### **数据安全**
- **输入验证**: 严格的输入参数验证
- **SQL注入防护**: 使用ORM防止SQL注入
- **XSS防护**: 输出内容转义处理
- **CORS配置**: 跨域请求安全控制

### **API安全**
- **速率限制**: 防止API滥用
- **请求大小限制**: 防止大文件攻击
- **错误处理**: 安全的错误信息返回

## 🚀 **部署指南**

### **开发环境**
```bash
# 启动开发服务器
python main.py
```

### **生产环境**
```bash
# 使用 Gunicorn
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker

# 使用 Docker
docker build -t akshare-mcp-adapter .
docker run -p 8000:8000 akshare-mcp-adapter
```

### **环境配置**
- **开发环境**: 启用调试模式，详细日志
- **生产环境**: 关闭调试，优化性能
- **测试环境**: 使用模拟数据，快速测试

## 📈 **性能优化**

### **缓存策略**
- **数据缓存**: 缓存频繁访问的金融数据
- **结果缓存**: 缓存LLM分析结果
- **TTL设置**: 根据数据特性设置过期时间

### **并发优化**
- **异步处理**: 使用 asyncio 提高并发性能
- **连接池**: 数据库连接池管理
- **负载均衡**: 支持多实例部署

### **资源优化**
- **内存管理**: 及时释放大对象
- **CPU优化**: 避免阻塞操作
- **网络优化**: 压缩响应数据

## 🔄 **维护指南**

### **日志管理**
- **日志级别**: DEBUG, INFO, WARNING, ERROR
- **日志轮转**: 自动日志文件轮转
- **结构化日志**: JSON格式日志输出

### **备份策略**
- **数据库备份**: 定期自动备份
- **配置备份**: 版本控制管理
- **日志归档**: 长期日志存储

### **更新流程**
1. **代码更新**: Git版本控制
2. **依赖更新**: 定期更新依赖包
3. **配置迁移**: 平滑配置升级
4. **数据迁移**: 数据库结构升级

## 📞 **技术支持**

### **常见问题**
- **LLM不可用**: 检查API密钥配置
- **数据获取失败**: 检查网络连接
- **认证失败**: 检查令牌有效性
- **性能问题**: 检查系统资源

### **故障排查**
1. **检查日志**: 查看错误日志
2. **健康检查**: 验证服务状态
3. **配置验证**: 确认配置正确
4. **依赖检查**: 验证依赖安装

### **联系方式**
- **GitHub**: https://github.com/sys3222/akshare-mcp-adapter
- **Issues**: 提交问题和建议
- **Wiki**: 详细技术文档

---

**版本**: 1.0.0  
**更新时间**: 2025-07-16  
**维护者**: AkShare MCP Adapter Team
