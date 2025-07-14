
import pytest
from src.data_processor import clean_financial_data

def test_null_handling():
    """测试空值处理"""
    raw = [10.5, None, 8.2]
    cleaned = clean_financial_data(raw)
    assert cleaned == [10.5, 0.0, 8.2]

def test_negative_values():
    """测试负值转换"""
    assert clean_financial_data([-1.5]) == [1.5]

def test_data_types():
    """测试数据类型转换"""
    assert clean_financial_data(["10.5"]) == [10.5]
