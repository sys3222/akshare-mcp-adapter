"""测试配置文件"""

import pytest
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

@pytest.fixture(scope="session")
def test_data_dir():
    """测试数据目录"""
    return Path(__file__).parent / "test_data"

@pytest.fixture
def sample_market_data():
    """示例市场数据"""
    import pandas as pd
    import numpy as np
    
    dates = pd.date_range('2024-01-01', periods=100)
    return pd.DataFrame({
        'date': dates,
        'close': 100 + np.random.randn(100).cumsum(),
        'volume': np.random.randint(1000, 10000, 100)
    })
