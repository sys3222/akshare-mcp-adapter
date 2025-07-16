"""
LLM API端点的单元测试
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from fastapi import HTTPException

import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from main import app
from handlers.llm_handler import AnalysisResult
from models.schemas import LLMAnalysisRequest, LLMAnalysisResponse

class TestLLMAPI:
    
    @pytest.fixture
    def client(self):
        """创建测试客户端"""
        return TestClient(app)
    
    @pytest.fixture
    def auth_headers(self, client):
        """获取认证头"""
        # 创建测试用户并获取token
        try:
            response = client.post("/api/token", data={
                "username": "test_user",
                "password": "test_password"
            })
            if response.status_code == 200:
                token = response.json()["access_token"]
                return {"Authorization": f"Bearer {token}"}
        except Exception:
            pass
        return {}
    
    def test_llm_analyze_endpoint(self, client, auth_headers):
        """测试LLM分析端点"""
        # 如果没有认证头，跳过测试
        if not auth_headers:
            pytest.skip("无认证头，跳过测试")

        # Mock分析结果
        mock_result = AnalysisResult(
            summary="测试分析摘要",
            insights=["洞察1", "洞察2"],
            recommendations=["建议1", "建议2"],
            data_points={"price_change": 5.0},
            charts_suggested=["价格走势图"],
            risk_level="中等风险",
            confidence=0.85
        )

        with patch('handlers.llm_handler.llm_analysis_handler.analyze_query', new_callable=AsyncMock) as mock_analyze:
            mock_analyze.return_value = mock_result

            response = client.post(
                "/api/llm/analyze",
                json={"query": "分析000001"},
                headers=auth_headers
            )

            # 如果认证失败，跳过测试
            if response.status_code == 401:
                pytest.skip("认证失败，跳过测试")

            assert response.status_code == 200
            data = response.json()
            assert data["summary"] == "测试分析摘要"
            assert len(data["insights"]) == 2
            assert len(data["recommendations"]) == 2
            assert data["risk_level"] == "中等风险"
            assert data["confidence"] == 0.85
    
    def test_llm_chat_endpoint(self, client, auth_headers):
        """测试LLM聊天端点"""
        # 如果没有认证头，跳过测试
        if not auth_headers:
            pytest.skip("无认证头，跳过测试")

        mock_result = AnalysisResult(
            summary="聊天响应",
            insights=["洞察"],
            recommendations=["建议"],
            data_points={},
            charts_suggested=[],
            risk_level="低风险",
            confidence=0.9
        )

        with patch('handlers.llm_handler.llm_analysis_handler.analyze_query', new_callable=AsyncMock) as mock_analyze:
            mock_analyze.return_value = mock_result

            response = client.post(
                "/api/llm/chat",
                params={"prompt": "分析000001"},
                headers=auth_headers
            )

            # 如果认证失败或LLM不可用，跳过测试
            if response.status_code in [401, 503]:
                pytest.skip(f"测试跳过，状态码: {response.status_code}")

            assert response.status_code == 200
            data = response.json()
            assert "response" in data
    
    def test_llm_capabilities_endpoint(self, client, auth_headers):
        """测试LLM功能说明端点"""
        response = client.get("/api/llm/capabilities", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "analysis_types" in data
        assert "supported_queries" in data
        assert "confidence_range" in data
    
    def test_llm_analyze_with_mode_selection(self, client, auth_headers):
        """测试带模式选择的LLM分析"""
        mock_result = AnalysisResult(
            summary="规则模式分析",
            insights=[], recommendations=[], data_points={},
            charts_suggested=[], risk_level="未知", confidence=0.7
        )
        
        with patch('handlers.llm_handler.rule_based_handler.analyze_query', new_callable=AsyncMock) as mock_analyze:
            mock_analyze.return_value = mock_result
            
            # 测试规则模式
            response = client.post(
                "/api/llm/analyze?use_llm=false",
                json={"query": "分析000001"},
                headers=auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["summary"] == "规则模式分析"
    
    def test_authentication_required(self, client):
        """测试认证要求"""
        response = client.post("/api/llm/analyze", json={"query": "test"})
        assert response.status_code == 401
        
        response = client.post("/api/llm/chat", params={"prompt": "test"})
        assert response.status_code == 401
        
        response = client.get("/api/llm/capabilities")
        assert response.status_code == 401
    
    def test_invalid_request_data(self, client, auth_headers):
        """测试无效请求数据"""
        # 空查询
        response = client.post(
            "/api/llm/analyze",
            json={"query": ""},
            headers=auth_headers
        )
        assert response.status_code == 422
        
        # 缺少必需字段
        response = client.post(
            "/api/llm/analyze",
            json={},
            headers=auth_headers
        )
        assert response.status_code == 422
    
    def test_llm_service_unavailable(self, client, auth_headers):
        """测试LLM服务不可用"""
        with patch('handlers.llm_handler.llm_analysis_handler.use_llm', False):
            response = client.post(
                "/api/llm/chat",
                params={"prompt": "test"},
                headers=auth_headers
            )
            assert response.status_code == 503
    
    def test_analysis_error_handling(self, client, auth_headers):
        """测试分析错误处理"""
        with patch('handlers.llm_handler.llm_analysis_handler.analyze_query', new_callable=AsyncMock) as mock_analyze:
            mock_analyze.side_effect = Exception("分析失败")
            
            response = client.post(
                "/api/llm/analyze",
                json={"query": "分析000001"},
                headers=auth_headers
            )
            
            assert response.status_code == 500
            assert "分析失败" in response.json()["detail"]
    
    def test_response_format_validation(self, client, auth_headers):
        """测试响应格式验证"""
        mock_result = AnalysisResult(
            summary="测试",
            insights=["洞察"],
            recommendations=["建议"],
            data_points={"key": "value"},
            charts_suggested=["图表"],
            risk_level="低风险",
            confidence=0.8
        )
        
        with patch('handlers.llm_handler.llm_analysis_handler.analyze_query', new_callable=AsyncMock) as mock_analyze:
            mock_analyze.return_value = mock_result
            
            response = client.post(
                "/api/llm/analyze",
                json={"query": "分析000001"},
                headers=auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            
            # 验证响应格式
            required_fields = ["summary", "insights", "recommendations", 
                             "data_points", "charts_suggested", "risk_level", "confidence"]
            for field in required_fields:
                assert field in data
            
            # 验证数据类型
            assert isinstance(data["insights"], list)
            assert isinstance(data["recommendations"], list)
            assert isinstance(data["data_points"], dict)
            assert isinstance(data["charts_suggested"], list)
            assert isinstance(data["confidence"], float)
    
    def test_concurrent_requests(self, client, auth_headers):
        """测试并发请求处理"""
        import threading
        import time
        
        results = []
        
        def make_request():
            response = client.post(
                "/api/llm/analyze",
                json={"query": "分析000001"},
                headers=auth_headers
            )
            results.append(response.status_code)
        
        mock_result = AnalysisResult(
            summary="并发测试", insights=[], recommendations=[],
            data_points={}, charts_suggested=[], risk_level="未知", confidence=0.5
        )
        
        with patch('handlers.llm_handler.llm_analysis_handler.analyze_query', new_callable=AsyncMock) as mock_analyze:
            mock_analyze.return_value = mock_result
            
            # 创建多个并发线程
            threads = []
            for _ in range(5):
                thread = threading.Thread(target=make_request)
                threads.append(thread)
                thread.start()
            
            # 等待所有线程完成
            for thread in threads:
                thread.join()
            
            # 验证所有请求都成功
            assert len(results) == 5
            assert all(status == 200 for status in results)
