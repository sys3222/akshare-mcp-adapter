"""
Mock数据生成器，用于测试夜间缓存更新功能
避免在测试时真实调用AkShare API
"""

import pandas as pd
from datetime import datetime, timedelta
import numpy as np

def generate_mock_stock_data(symbol="000001", start_date="20240101", end_date="20240107"):
    """生成模拟股票历史数据"""
    start = datetime.strptime(start_date, "%Y%m%d")
    end = datetime.strptime(end_date, "%Y%m%d")
    
    # 生成日期序列（只包含工作日）
    dates = pd.bdate_range(start=start, end=end)
    
    # 生成模拟价格数据
    np.random.seed(42)  # 确保测试结果可重现
    base_price = 10.0
    
    data = []
    for i, date in enumerate(dates):
        # 模拟价格波动
        price_change = np.random.normal(0, 0.02)  # 2%的日波动率
        base_price *= (1 + price_change)
        
        # 生成OHLC数据
        open_price = base_price * (1 + np.random.normal(0, 0.005))
        high_price = max(open_price, base_price) * (1 + abs(np.random.normal(0, 0.01)))
        low_price = min(open_price, base_price) * (1 - abs(np.random.normal(0, 0.01)))
        close_price = base_price
        volume = np.random.randint(1000000, 10000000)
        
        data.append({
            "日期": date.strftime("%Y-%m-%d"),
            "开盘": round(open_price, 2),
            "收盘": round(close_price, 2),
            "最高": round(high_price, 2),
            "最低": round(low_price, 2),
            "成交量": volume,
            "成交额": round(volume * close_price, 2),
            "振幅": round(abs(high_price - low_price) / close_price * 100, 2),
            "涨跌幅": round(price_change * 100, 2),
            "涨跌额": round(close_price * price_change, 2),
            "换手率": round(np.random.uniform(0.5, 5.0), 2)
        })
    
    return pd.DataFrame(data)

def generate_mock_index_data(symbol="000001", start_date="20240101", end_date="20240107"):
    """生成模拟指数历史数据"""
    start = datetime.strptime(start_date, "%Y%m%d")
    end = datetime.strptime(end_date, "%Y%m%d")
    
    dates = pd.bdate_range(start=start, end=end)
    
    np.random.seed(42)
    base_value = 3000.0  # 指数基准值
    
    data = []
    for i, date in enumerate(dates):
        value_change = np.random.normal(0, 0.015)  # 1.5%的日波动率
        base_value *= (1 + value_change)
        
        open_value = base_value * (1 + np.random.normal(0, 0.003))
        high_value = max(open_value, base_value) * (1 + abs(np.random.normal(0, 0.008)))
        low_value = min(open_value, base_value) * (1 - abs(np.random.normal(0, 0.008)))
        close_value = base_value
        
        data.append({
            "日期": date.strftime("%Y-%m-%d"),
            "开盘": round(open_value, 2),
            "收盘": round(close_value, 2),
            "最高": round(high_value, 2),
            "最低": round(low_value, 2),
            "成交量": np.random.randint(100000000, 500000000),
            "成交额": np.random.randint(200000000000, 800000000000),
            "振幅": round(abs(high_value - low_value) / close_value * 100, 2),
            "涨跌幅": round(value_change * 100, 2),
            "涨跌额": round(close_value * value_change, 2)
        })
    
    return pd.DataFrame(data)

def generate_mock_spot_data():
    """生成模拟实时行情数据"""
    np.random.seed(42)
    
    # 模拟100只股票的实时数据
    data = []
    for i in range(100):
        code = f"{i:06d}"
        name = f"测试股票{i:03d}"
        price = round(np.random.uniform(5, 100), 2)
        change_pct = round(np.random.normal(0, 3), 2)
        
        data.append({
            "代码": code,
            "名称": name,
            "最新价": price,
            "涨跌幅": change_pct,
            "涨跌额": round(price * change_pct / 100, 2),
            "成交量": np.random.randint(1000, 100000),
            "成交额": np.random.randint(1000000, 100000000),
            "振幅": round(np.random.uniform(0.5, 8.0), 2),
            "最高": round(price * (1 + abs(change_pct) / 200), 2),
            "最低": round(price * (1 - abs(change_pct) / 200), 2),
            "今开": round(price * (1 + np.random.normal(0, 0.01)), 2),
            "昨收": round(price / (1 + change_pct / 100), 2)
        })
    
    return pd.DataFrame(data)

# 接口映射表
MOCK_DATA_GENERATORS = {
    "stock_zh_a_hist": generate_mock_stock_data,
    "index_zh_a_hist": generate_mock_index_data,
    "stock_zh_a_spot_em": lambda **kwargs: generate_mock_spot_data(),
    "fund_etf_spot_em": lambda **kwargs: generate_mock_spot_data(),
}

def get_mock_data(interface, **params):
    """根据接口名称获取对应的Mock数据"""
    if interface in MOCK_DATA_GENERATORS:
        return MOCK_DATA_GENERATORS[interface](**params)
    else:
        # 返回空DataFrame作为默认值
        return pd.DataFrame()
