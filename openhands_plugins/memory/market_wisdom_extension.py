"""市场常识Memory扩展"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import re

class RecallAction:
    """召回动作"""
    
    def __init__(self, query: str, recall_type: str = "market_wisdom"):
        self.query = query
        self.recall_type = recall_type
        self.timestamp = datetime.now()

class RecallObservation:
    """召回观察结果"""
    
    def __init__(self, content: str, recall_type: str, metadata: Dict[str, Any] = None):
        self.content = content
        self.recall_type = recall_type
        self.metadata = metadata or {}
        self.timestamp = datetime.now()

class KnowledgeMicroagent:
    """知识微代理"""
    
    def __init__(self, name: str, content: str, triggers: List[str] = None):
        self.name = name
        self.content = content
        self.triggers = triggers or []
        self.created_at = datetime.now()
        self.last_accessed = None
        self.access_count = 0
    
    def is_triggered(self, query: str) -> bool:
        """检查是否被查询触发"""
        query_lower = query.lower()
        
        for trigger in self.triggers:
            if trigger.lower() in query_lower:
                return True
        
        return False
    
    def access(self):
        """记录访问"""
        self.last_accessed = datetime.now()
        self.access_count += 1

class MarketWisdomExtension:
    """市场常识Memory扩展
    
    为OpenHands Memory系统提供量化投资领域的专业知识支持
    """
    
    def __init__(self, memory=None):
        self.memory = memory
        self.wisdom_cache = {}
        self.last_update_check = None
        
        # 市场常识分类触发器
        self.wisdom_triggers = {
            'correlations': ['相关性', 'correlation', '关联', '联动'],
            'macro_indicators': ['宏观', 'macro', '经济指标', '利率', '通胀'],
            'sector_rotation': ['板块', 'sector', '轮动', 'rotation', '行业'],
            'risk_sentiment': ['风险', 'risk', '情绪', 'sentiment', 'vix'],
            'market_regime': ['市场', 'regime', '牛市', '熊市', '震荡']
        }
        
        # 初始化示例知识
        self._initialize_sample_wisdom()
    
    def _initialize_sample_wisdom(self):
        """初始化示例市场常识"""
        
        # 资产相关性知识
        correlations_agent = KnowledgeMicroagent(
            name='asset_correlations',
            content="""
# 主要资产相关性

## 股债相关性
- 正常时期: -0.2 到 0.2
- 危机时期: 0.6 到 0.8
- 机制: 避险情绪驱动

## 美元与大宗商品
- 长期相关性: -0.7
- 机制: 美元定价效应

## VIX与股市
- 相关性: -0.75
- 机制: 恐慌指数反向指示
            """,
            triggers=['相关性', 'correlation', 'VIX', '股债', '美元']
        )
        
        # 宏观指标知识
        macro_agent = KnowledgeMicroagent(
            name='macro_indicators',
            content="""
# 关键宏观指标

## 利率影响
- 加息周期: 成长股承压，价值股受益
- 降息周期: 成长股受益，债券上涨

## 通胀指标
- CPI > 3%: 通胀压力显现
- PPI领先CPI约1-2个月

## 就业数据
- 非农就业: 月度关键指标
- 失业率: 滞后指标
            """,
            triggers=['宏观', 'macro', '利率', '通胀', 'CPI', 'PPI', '就业']
        )
        
        self.add_wisdom_microagent(correlations_agent)
        self.add_wisdom_microagent(macro_agent)
    
    def add_wisdom_microagent(self, microagent: KnowledgeMicroagent):
        """添加知识微代理"""
        if hasattr(self.memory, 'knowledge_microagents'):
            self.memory.knowledge_microagents[microagent.name] = microagent
        else:
            # 如果memory没有knowledge_microagents属性，创建本地存储
            if not hasattr(self, '_local_microagents'):
                self._local_microagents = {}
            self._local_microagents[microagent.name] = microagent
    
    def recall_market_wisdom(self, action: RecallAction) -> Optional[RecallObservation]:
        """召回市场常识"""
        
        query = action.query.lower()
        wisdom_type = self._identify_wisdom_type(query)
        
        # 查找匹配的知识微代理
        relevant_content = []
        microagents = self._get_microagents()
        
        for name, agent in microagents.items():
            if agent.is_triggered(query):
                agent.access()
                relevant_content.append(agent.content)
        
        if relevant_content:
            combined_content = "\n\n".join(relevant_content)
            
            metadata = {
                'wisdom_type': wisdom_type,
                'query': action.query,
                'source': 'market_wisdom_extension',
                'microagents_used': len(relevant_content),
                'timestamp': datetime.now().isoformat()
            }
            
            return RecallObservation(
                content=combined_content,
                recall_type=action.recall_type,
                metadata=metadata
            )
        
        return None
    
    def _identify_wisdom_type(self, query: str) -> Optional[str]:
        """识别查询的智慧类型"""
        
        for wisdom_type, triggers in self.wisdom_triggers.items():
            for trigger in triggers:
                if trigger in query:
                    return wisdom_type
        
        return None
    
    def _get_microagents(self) -> Dict[str, KnowledgeMicroagent]:
        """获取所有微代理"""
        
        if hasattr(self.memory, 'knowledge_microagents'):
            return self.memory.knowledge_microagents
        elif hasattr(self, '_local_microagents'):
            return self._local_microagents
        else:
            return {}
    
    def get_correlation_wisdom(self, asset1: str, asset2: str) -> Dict[str, Any]:
        """获取特定资产间的相关性智慧"""
        
        # 简化的相关性查询
        query = f"{asset1}与{asset2}的相关性"
        action = RecallAction(query=query)
        observation = self.recall_market_wisdom(action)
        
        if observation:
            # 尝试从内容中提取相关性数值
            correlation_match = re.search(r'相关性[：:]\s*(-?\d+\.\d+)', observation.content)
            correlation = float(correlation_match.group(1)) if correlation_match else None
            
            return {
                'assets': [asset1, asset2],
                'correlation': correlation,
                'source': 'market_wisdom',
                'confidence': 'high' if correlation else 'low',
                'details': observation.content
            }
        
        return {
            'assets': [asset1, asset2],
            'correlation': None,
            'source': 'market_wisdom',
            'confidence': 'none',
            'details': 'No relevant wisdom found'
        }
    
    def get_wisdom_statistics(self) -> Dict[str, Any]:
        """获取智慧统计信息"""
        
        microagents = self._get_microagents()
        
        return {
            'total_microagents': len(microagents),
            'wisdom_types': list(self.wisdom_triggers.keys()),
            'cache_size': len(self.wisdom_cache),
            'microagent_names': list(microagents.keys()),
            'last_update': self.last_update_check.isoformat() if self.last_update_check else None
        }
    
    def update_wisdom_cache(self):
        """更新智慧缓存"""
        self.last_update_check = datetime.now()
        # 这里可以添加从外部数据源更新的逻辑
