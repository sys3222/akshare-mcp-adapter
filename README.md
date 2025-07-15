# MCP 统一服务 - AkShare数据 + 量化回测 v3.1.0

一个统一的MCP (Microservice Control Protocol) 服务，提供三大核心功能：
1. **AkShare数据接口** - 通过标准化MCP协议访问中国金融市场数据
2. **量化回测服务** - 基于Backtrader的策略回测和性能分析
3. **用户文件管理** - 支持用户上传和管理自己的数据文件，用于浏览和分析

## 🚀 核心功能

### 📊 AkShare数据接口 (MCP协议)
- **用户认证 (OAuth2/JWT)**: 通过Token保护核心API接口，确保服务安全。
- **数据缓存**: 内置文件缓存机制，显著提升常用数据的响应速度。
- **数据大小限制**: 对API获取的数据强制实施10MB的大小限制，防止服务过载。

### 📂 数据管理与浏览 (新增)
- **用户文件隔离**: 每个用户拥有独立的存储空间 (`static/cache/{username}`), 确保数据私密性。
- **文件增删查**: 提供API和界面来上传、列出和删除用户自己的数据文件。
- **在线数据浏览**: 支持在Web界面���直接浏览上传的CSV文件内容，支持分页。
- **文件大小限制**: 上传文件限制为10MB以内。

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
# 1. 安装依赖
pip install -r requirements.txt

# 2. 创建一个初始用户
python create_user.py --username your_user --password your_password

# 3. 启动服务
python main.py
```

## 📖 API接口

所有API端点都以 `/api` 为前缀，并且大部分需要认证。

### 1. 认证接口
- `POST /api/token`: 获取Token。
- `GET /api/users/me`: 获取当前用户信息。

### 2. 数据获取 (API)
- `POST /api/mcp-data`: 通过MCP协议从AkShare获取数据。

### 3. 数据管理 (用户文件)
- `POST /api/data/upload`: 上传一个数据文件 (CSV)。
- `GET /api/data/files`: 列出当前用户所有已上传的��件。
- `DELETE /api/data/files/{filename}`: 删除一个指定的文件。
- `POST /api/data/explore/{filename}`: 浏览已上传文件的数据内容，支持分页。

### 4. 回测接口
- `POST /api/backtest-with-mcp`: 使用AkShare数据源进行回测。

### 5. 系统接口
- `GET /api/health`: 健康检查。
- `GET /api/interfaces`: 获取可用的AkShare接口配置。

## 🖥️ Web界面功能

一个功能完善的单页应用，提供以下功能：

1. **用户认证** - 提供登录界面，管理访问权限。
2. **数据分析** - 分为两大模块：
    - **数据获取**: 调用AkShare接口获取实时或历史数据。
    - **我的数据文件**: 上传、管理和浏览用户自己的数据文件。
3. **回测** - 支持多种回测方式：
    - 上传策略和数据文件。
    - 直接使用AkShare数据源进行回测。
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

# 3. (重要) 创建一个初始用户
python create_user.py --username your_user --password your_password

# 4. 启动服务
python main.py
```

### Docker部署
```bash
# 构建镜像
docker build -t mcp-unified-service .

# 运行容器 (注意: Docker环境下的用户创建需要进入容器执行)
docker run -p 12001:12001 mcp-unified-service
# docker exec -it <container_id> python create_user.py --username user --password pass
```

## 🔧 开发和测试

### 项目结构
```
├── api/                  # API路由 (FastAPI)
├── handlers/             # 业务逻辑处理器
├── core/                 # 核心功能 (回测引擎、MCP协议、安全)
├── models/               # 数据模型 (Pydantic)
├── static/               # Web界面 (HTML/JS/CSS)
│   └── cache/            # 用户文件缓存目录
├── tests/                # 单元测试和集成测试
├── main.py               # 服务入口
└── create_user.py        # 用户创建脚本
```

### 运行测试
项目包含一套完整的单元测试和集成测试，使用 `pytest` 框架。

```bash
# 运行所有测试
pytest
```

## 📝 更新日志

### v3.2.0 (最新)
- ✨ **增强 测试覆盖率**: 为 `core` 和 `handlers` 目录增加了全面的单元测试，确保代码质量和稳定性。
- ✨ **优化 数据获取**: 为 AkShare 数据接口增加了 `tenacity` 重试机制，提升了在网络不稳定情况下的数据获取成功率。
- ✨ **重构 错误处理**: 优化了 `mcp_handler` 的错误处理逻辑，使其更加清晰和健壮。

### v3.1.0
- ✨ **新增 数据管理功能**: 用户现在可以上传、删除和浏览自己的数据文件。
- ✨ **新增 用户文件隔离**: 文件存储在 `static/cache/{username}` 目录下，确保用户数据私密性。
- ✨ **新增 数据大小限制**: 对API获取和文件上传增加了10MB的限制，以保证服务性能。
- ✨ **重构 数据分析界面**: 将“数据分析”功能拆分为“数据获取(API)”和“我的数据文件”两个子模块。
- ✨ **完善 自动化测试**: 为新的文件管理API增加了完整的集成测试，并引入了用户认证测试流程。

### v3.0.0
- ✨ **新增 认证与授权**: 引入OAuth2/JWT保护核心API，提升服务安全性。
- ✨ **新增 数据缓存机制**: 为AkShare接口增加文件缓存，大幅提升重复数据请求的响应速度。
- ✨ **重构 Web用户界面**: `index.html` 全面升级为单页应用，支持用户登录、多种回测模式和交互式结果展示。

---

**GitHub仓库**: https://github.com/sys3222/akshare-mcp-adapter