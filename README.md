# AKShare MCP 适配服务

## 服务状态
- 开发模式：`python run.py dev` (支持热重载)
- 生产模式：`python run.py prod` (4 workers)

## 接口文档
访问 http://localhost:3001/docs 查看Swagger文档

## 常用命令
```bash
# 测试股票接口
curl -X POST http://localhost:3001/api/mcp \\
-H "Content-Type: application/json" \\
-d '{
    "interface": "stock_zh_a_hist",
    "params": {"symbol": "000001", "period": "daily"},
    "request_id": "test001"
}'

# 测试基金接口  
curl -X POST http://localhost:3001/api/mcp \\
-H "Content-Type: application/json" \\
-d '{
    "interface": "fund_em_open_fund_info",
    "params": {"fund": "000001", "indicator": "单位净值走势"},
    "request_id": "test002"
}'
```

## 部署说明
1. 安装依赖：`pip install -r requirements.txt`
2. 开发测试：`python run.py dev`
3. 生产部署：`python run.py prod`
