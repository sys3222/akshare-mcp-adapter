# AkShare代码执行接口示例

本目录包含使用AkShare代码执行接口的示例代码和文档。

## 接口说明

AkShare代码执行接口允许用户直接提交AkShare代码片段，服务器执行代码并返回结果。这种方式比传统的API调用更加灵活，用户可以自定义数据处理逻辑。

### 接口地址
```
POST /api/execute-akshare
```

### 请求参数
```json
{
  "code": "import akshare as ak\ndf = ak.stock_zh_a_spot()\ndf",
  "format": "json"  // 可选值: "json", "csv", "html"
}
```

### 响应格式
```json
{
  "result": [...],  // 执行结果，根据format参数返回不同格式
  "format": "json",  // 结果格式
  "error": null  // 错误信息，如果执行成功则为null
}
```

## 使用示例

### 1. 获取深圳A股实时行情

```python
import requests

url = "http://localhost:12001/api/execute-akshare"
payload = {
    "code": """
import akshare as ak
stock_sz_a_spot_em_df = ak.stock_sz_a_spot_em()
stock_sz_a_spot_em_df
    """,
    "format": "json"
}

response = requests.post(url, json=payload)
result = response.json()

# 处理结果
if not result.get("error"):
    data = result["result"]
    print(f"获取到 {len(data)} 只深圳A股")
else:
    print(f"错误: {result['error']}")
```

### 2. 获取股票历史数据并计算技术指标

```python
import requests

url = "http://localhost:12001/api/execute-akshare"
payload = {
    "code": """
import akshare as ak
import pandas as pd

# 获取股票数据
stock_df = ak.stock_zh_a_hist(symbol="sh601318", period="daily", 
                             start_date="20230101", end_date="20231231", 
                             adjust="qfq")

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
result_df = stock_df[['日期', '开盘', '收盘', '最高', '最低', '成交量', 
                     'MA5', 'MA10', 'MA20', 'MACD', 'Signal', 'Histogram']]

# 返回处理后的数据
result_df
    """,
    "format": "json"
}

response = requests.post(url, json=payload)
result = response.json()

# 处理结果
if not result.get("error"):
    data = result["result"]
    print(f"获取到 {len(data)} 条处理后的数据")
else:
    print(f"错误: {result['error']}")
```

### 3. 获取CSV格式数据

```python
import requests
import pandas as pd
from io import StringIO

url = "http://localhost:12001/api/execute-akshare"
payload = {
    "code": """
import akshare as ak
stock_zh_index_daily_df = ak.stock_zh_index_daily(symbol="sh000001")
stock_zh_index_daily_df
    """,
    "format": "csv"
}

response = requests.post(url, json=payload)
result = response.json()

# 处理结果
if not result.get("error"):
    # 将CSV字符串转换为DataFrame
    df = pd.read_csv(StringIO(result["result"]))
    print(f"数据形状: {df.shape}")
    print(df.head())
else:
    print(f"错误: {result['error']}")
```

## 更多示例

请查看 `akshare_code_examples.py` 文件，其中包含更多使用示例。

## 注意事项

1. 代码执行在服务器端进行，请确保代码安全，不包含恶意操作
2. 代码执行有超时限制，请避免执行耗时过长的操作
3. 返回的数据量较大时，建议使用分页或限制返回字段
4. 如果需要频繁调用相同的代码，建议使用缓存机制减少服务器负载