#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
AkShare代码执行接口示例

本文件包含多个示例，展示如何使用AkShare代码执行接口获取各种金融数据。
"""

import requests
import json
import pandas as pd
from io import StringIO

# 服务地址
BASE_URL = "http://localhost:12001"

def execute_akshare_code(code, format="json"):
    """
    执行AkShare代码并获取结果
    
    Args:
        code: AkShare代码字符串
        format: 输出格式，支持 "json", "csv", "html"
        
    Returns:
        根据format参数返回不同格式的结果
    """
    url = f"{BASE_URL}/api/execute-akshare"
    payload = {
        "code": code,
        "format": format
    }
    
    response = requests.post(url, json=payload)
    result = response.json()
    
    if result.get("error"):
        print(f"Error: {result['error']}")
        return None
    
    # 根据格式处理结果
    if format == "json":
        return result["result"]
    elif format == "csv":
        return pd.read_csv(StringIO(result["result"]))
    elif format == "html":
        return result["result"]
    else:
        return result["result"]

# 示例1: 获取深圳A股实时行情
def get_sz_a_spot():
    code = """
import akshare as ak

# 获取深圳A股实时行情
stock_sz_a_spot_em_df = ak.stock_sz_a_spot_em()
stock_sz_a_spot_em_df
"""
    return execute_akshare_code(code, "json")

# 示例2: 获取上证指数历史数据
def get_sh_index_hist():
    code = """
import akshare as ak

# 获取上证指数历史数据
stock_zh_index_daily_df = ak.stock_zh_index_daily(symbol="sh000001")
stock_zh_index_daily_df
"""
    return execute_akshare_code(code, "csv")

# 示例3: 获取股票板块行情
def get_stock_sectors():
    code = """
import akshare as ak

# 获取股票板块行情
stock_sector_spot_df = ak.stock_sector_spot()
stock_sector_spot_df
"""
    return execute_akshare_code(code, "html")

# 示例4: 获取特定股票的K线数据
def get_stock_kline(symbol="sh601318", period="daily", start_date="20230101", end_date="20231231"):
    code = f"""
import akshare as ak

# 获取特定股票的K线数据
stock_zh_a_hist_df = ak.stock_zh_a_hist(
    symbol="{symbol}", 
    period="{period}", 
    start_date="{start_date}", 
    end_date="{end_date}", 
    adjust="qfq"
)
stock_zh_a_hist_df
"""
    return execute_akshare_code(code, "json")

# 示例5: 获取宏观经济数据
def get_macro_data():
    code = """
import akshare as ak

# 获取中国宏观经济数据-CPI
macro_china_cpi_df = ak.macro_china_cpi()
macro_china_cpi_df
"""
    return execute_akshare_code(code, "json")

# 示例6: 自定义数据处理
def custom_data_processing():
    code = """
import akshare as ak
import pandas as pd

# 获取股票数据
stock_df = ak.stock_zh_a_hist(symbol="sh601318", period="daily", start_date="20230101", end_date="20231231", adjust="qfq")

# 计算移动平均线
stock_df['MA5'] = stock_df['收盘'].rolling(window=5).mean()
stock_df['MA10'] = stock_df['收盘'].rolling(window=10).mean()
stock_df['MA20'] = stock_df['收盘'].rolling(window=20).mean()

# 计算MACD
def calculate_macd(df, fast_period=12, slow_period=26, signal_period=9):
    df['EMA_fast'] = df['收盘'].ewm(span=fast_period, adjust=False).mean()
    df['EMA_slow'] = df['收盘'].ewm(span=slow_period, adjust=False).mean()
    df['MACD'] = df['EMA_fast'] - df['EMA_slow']
    df['Signal'] = df['MACD'].ewm(span=signal_period, adjust=False).mean()
    df['Histogram'] = df['MACD'] - df['Signal']
    return df

stock_df = calculate_macd(stock_df)

# 只保留需要的列
result_df = stock_df[['日期', '开盘', '收盘', '最高', '最低', '成交量', 'MA5', 'MA10', 'MA20', 'MACD', 'Signal', 'Histogram']]

# 返回处理后的数据
result_df
"""
    return execute_akshare_code(code, "json")

if __name__ == "__main__":
    print("\n=== 示例1: 获取深圳A股实时行情 ===")
    sz_stocks = get_sz_a_spot()
    print(f"获取到 {len(sz_stocks)} 只深圳A股")
    print(f"前5只股票: {json.dumps(sz_stocks[:5], indent=2, ensure_ascii=False)}")
    
    print("\n=== 示例2: 获取上证指数历史数据 ===")
    sh_index = get_sh_index_hist()
    print(f"上证指数数据形状: {sh_index.shape}")
    print(sh_index.head())
    
    print("\n=== 示例3: 获取股票板块行情 ===")
    sectors_html = get_stock_sectors()
    print(f"获取到HTML表格，长度: {len(sectors_html)} 字符")
    
    print("\n=== 示例4: 获取特定股票的K线数据 ===")
    kline_data = get_stock_kline("sh601318")
    print(f"获取到 {len(kline_data)} 条K线数据")
    print(f"前3条数据: {json.dumps(kline_data[:3], indent=2, ensure_ascii=False)}")
    
    print("\n=== 示例5: 获取宏观经济数据 ===")
    macro_data = get_macro_data()
    print(f"获取到 {len(macro_data)} 条宏观经济数据")
    print(f"前3条数据: {json.dumps(macro_data[:3], indent=2, ensure_ascii=False)}")
    
    print("\n=== 示例6: 自定义数据处理 ===")
    processed_data = custom_data_processing()
    print(f"获取到 {len(processed_data)} 条处理后的数据")
    print(f"前3条数据: {json.dumps(processed_data[:3], indent=2, ensure_ascii=False)}")