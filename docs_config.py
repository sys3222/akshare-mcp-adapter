from fastapi.openapi.utils import get_openapi

def custom_openapi(app):
    def wrapper():
        if app.openapi_schema:
            return app.openapi_schema
            
        openapi_schema = get_openapi(
            title="AKShare MCP服务",
            version="2.1.0",
            description="通过标准化协议提供金融数据接口",
            routes=app.routes,
        )
        
        # 添加自定义文档
        openapi_schema["info"]["x-logo"] = {
            "url": "https://akshare.akfamily.xyz/static/logo.png"
        }
        return openapi_schema
        
    return wrapper
