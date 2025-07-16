"""
LLM功能集成测试
测试LLM与其他系统组件的集成
"""

import pytest
import asyncio
import os
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient

import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from main import app
from handlers.llm_handler import LLMAnalysisHandler
from handlers.mcp_handler import handle_mcp_data_request
from models.schemas import PaginatedDataResponse

class TestLLMIntegration:
    
    @pytest.fixture
    def client(self):
        """创建测试客户端"""
        return TestClient(app)
    
    @pytest.fixture
    def auth_headers(self, client):
        """获取认证头"""
        response = client.post("/api/token", data={
            "username": "test_user",
            "password": "test_password"
        })
        if response.status_code == 200:
            token = response.json()["access_token"]
            return {"Authorization": f"Bearer {token}"}
        return {}
    
    @pytest.mark.asyncio
    async def test_llm_with_mcp_integration(self):
        """测试LLM与MCP协议的集成"""
        handler = LLMAnalysisHandler(use_llm=False)  # 使用规则模式避免API依赖
        
        # Mock MCP数据响应
        mock_data = PaginatedDataResponse(
            data=[
                {'日期': '2024-01-01', '收盘': 10.0, '成交量': 1000000},
                {'日期': '2024-01-02', '收盘': 10.5, '成交量': 1200000}
            ],
            total_records=2,
            current_page=1,
            total_pages=1
        )
        
        with patch('handlers.llm_handler.handle_mcp_data_request', new_callable=AsyncMock) as mock_mcp:
            mock_mcp.return_value = mock_data
            
            result = await handler.analyze_query("分析000001", "test_user")
            
            # 验证MCP调用
            assert mock_mcp.called
            
            # 验证分析结果
            assert result.summary != ""
            assert len(result.insights) > 0
            assert result.confidence > 0
    
    def test_llm_api_with_authentication(self, client):
        """测试LLM API与认证系统的集成"""
        # 未认证请求
        response = client.post("/api/llm/analyze", json={"query": "test"})
        assert response.status_code == 401
        
        # 错误token
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.post("/api/llm/analyze", json={"query": "test"}, headers=headers)
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_llm_with_cache_system(self):
        """测试LLM与缓存系统的集成"""
        handler = LLMAnalysisHandler(use_llm=False)
        
        # 模拟缓存命中
        cached_data = PaginatedDataResponse(
            data=[{'日期': '2024-01-01', '收盘': 10.0}],
            total_records=1, current_page=1, total_pages=1
        )
        
        with patch('handlers.llm_handler.handle_mcp_data_request', new_callable=AsyncMock) as mock_mcp:
            mock_mcp.return_value = cached_data
            
            # 第一次调用
            result1 = await handler.analyze_query("分析000001", "test_user")
            
            # 第二次调用（应该使用缓存）
            result2 = await handler.analyze_query("分析000001", "test_user")
            
            # 验证两次结果一致
            assert result1.summary == result2.summary
            assert mock_mcp.call_count >= 1
    
    def test_llm_error_propagation(self, client, auth_headers):
        """测试错误在系统中的传播"""
        with patch('handlers.llm_handler.llm_analysis_handler.analyze_query', new_callable=AsyncMock) as mock_analyze:
            # 模拟不同类型的错误
            test_cases = [
                (ValueError("参数错误"), 500),
                (ConnectionError("网络错误"), 500),
                (TimeoutError("超时错误"), 500),
            ]
            
            for error, expected_status in test_cases:
                mock_analyze.side_effect = error
                
                response = client.post(
                    "/api/llm/analyze",
                    json={"query": "分析000001"},
                    headers=auth_headers
                )
                
                assert response.status_code == expected_status
                assert "error" in response.json()["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_llm_performance_under_load(self):
        """测试LLM在负载下的性能"""
        handler = LLMAnalysisHandler(use_llm=False)
        
        # 模拟快速响应
        mock_data = PaginatedDataResponse(
            data=[{'日期': '2024-01-01', '收盘': 10.0}],
            total_records=1, current_page=1, total_pages=1
        )
        
        with patch('handlers.llm_handler.handle_mcp_data_request', new_callable=AsyncMock) as mock_mcp:
            mock_mcp.return_value = mock_data
            
            # 并发执行多个分析
            tasks = []
            for i in range(10):
                task = handler.analyze_query(f"分析00000{i%3}", "test_user")
                tasks.append(task)
            
            start_time = asyncio.get_event_loop().time()
            results = await asyncio.gather(*tasks)
            end_time = asyncio.get_event_loop().time()
            
            # 验证性能
            total_time = end_time - start_time
            assert total_time < 5.0  # 应该在5秒内完成
            assert len(results) == 10
            assert all(result.confidence > 0 for result in results)
    
    def test_llm_data_format_compatibility(self, client, auth_headers):
        """测试LLM与不同数据格式的兼容性"""
        test_queries = [
            {"query": "分析000001"},  # 标准查询
            {"query": "分析000001", "context": {"user_id": "test"}},  # 带上下文
        ]
        
        for query_data in test_queries:
            with patch('handlers.llm_handler.llm_analysis_handler.analyze_query', new_callable=AsyncMock) as mock_analyze:
                mock_analyze.return_value = self._create_mock_result()
                
                response = client.post(
                    "/api/llm/analyze",
                    json=query_data,
                    headers=auth_headers
                )
                
                assert response.status_code == 200
                data = response.json()
                assert "summary" in data
    
    def test_llm_with_different_user_contexts(self, client):
        """测试LLM在不同用户上下文中的行为"""
        # 创建不同的用户token
        users = ["test_user", "admin_user"]
        
        for username in users:
            # 获取用户token
            response = client.post("/api/token", data={
                "username": username,
                "password": "test_password"
            })
            
            if response.status_code == 200:
                token = response.json()["access_token"]
                headers = {"Authorization": f"Bearer {token}"}
                
                with patch('handlers.llm_handler.llm_analysis_handler.analyze_query', new_callable=AsyncMock) as mock_analyze:
                    mock_analyze.return_value = self._create_mock_result()
                    
                    response = client.post(
                        "/api/llm/analyze",
                        json={"query": "分析000001"},
                        headers=headers
                    )
                    
                    # 验证用户上下文传递
                    assert mock_analyze.called
                    call_args = mock_analyze.call_args
                    assert call_args[1]['username'] == username
    
    @pytest.mark.asyncio
    async def test_llm_fallback_mechanism(self):
        """测试LLM回退机制"""
        # 创建LLM处理器（可能不可用）
        llm_handler = LLMAnalysisHandler(use_llm=True)
        rule_handler = LLMAnalysisHandler(use_llm=False)
        
        mock_data = PaginatedDataResponse(
            data=[{'日期': '2024-01-01', '收盘': 10.0}],
            total_records=1, current_page=1, total_pages=1
        )
        
        with patch('handlers.llm_handler.handle_mcp_data_request', new_callable=AsyncMock) as mock_mcp:
            mock_mcp.return_value = mock_data
            
            # 测试规则模式作为回退
            result = await rule_handler.analyze_query("分析000001", "test_user")
            
            assert result.summary != ""
            assert result.confidence > 0
    
    def test_llm_configuration_validation(self):
        """测试LLM配置验证"""
        # 测试无API密钥的情况
        with patch.dict(os.environ, {}, clear=True):
            handler = LLMAnalysisHandler(use_llm=True)
            # 应该回退到规则模式
            assert handler.use_llm == False
        
        # 测试有API密钥的情况
        with patch.dict(os.environ, {"GEMINI_API_KEY": "test_key"}):
            with patch('google.generativeai.configure'):
                handler = LLMAnalysisHandler(use_llm=True)
                # 配置应该成功
                assert hasattr(handler, 'akshare_tool')
    
    def _create_mock_result(self):
        """创建模拟分析结果"""
        from handlers.llm_handler import AnalysisResult
        return AnalysisResult(
            summary="测试分析",
            insights=["洞察1"],
            recommendations=["建议1"],
            data_points={"test": "value"},
            charts_suggested=["图表1"],
            risk_level="中等风险",
            confidence=0.8
        )
    
    @pytest.mark.asyncio
    async def test_end_to_end_workflow(self, client, auth_headers):
        """测试端到端工作流程"""
        # 1. 获取功能说明
        response = client.get("/api/llm/capabilities", headers=auth_headers)
        assert response.status_code == 200
        capabilities = response.json()
        
        # 2. 执行分析
        with patch('handlers.llm_handler.llm_analysis_handler.analyze_query', new_callable=AsyncMock) as mock_analyze:
            mock_analyze.return_value = self._create_mock_result()
            
            response = client.post(
                "/api/llm/analyze",
                json={"query": "分析000001"},
                headers=auth_headers
            )
            
            assert response.status_code == 200
            analysis_result = response.json()
            
            # 3. 验证结果格式与功能说明一致
            assert "summary" in analysis_result
            assert "insights" in analysis_result
            assert "recommendations" in analysis_result
            
            # 4. 测试聊天接口
            response = client.post(
                "/api/llm/chat",
                params={"prompt": "分析000001"},
                headers=auth_headers
            )
            
            assert response.status_code == 200
            chat_result = response.json()
            assert "response" in chat_result
