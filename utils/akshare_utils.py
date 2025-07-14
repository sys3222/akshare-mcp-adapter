import os
import pandas as pd
import akshare as ak
import backtrader as bt
from datetime import datetime
import logging

logger = logging.getLogger("mcp-unified-service")

def init_akshare_cache():
    """
    Initialize AkShare cache directories and preload common data
    """
    # Create cache directories
    os.makedirs('etf_cache', exist_ok=True)
    os.makedirs('index_cache', exist_ok=True)
    os.makedirs('stock_cache', exist_ok=True)
    
    logger.info("初始化AkShare缓存目录")
    
    # Preload common indices (optional)
    try:
        # 预加载沪深300指数作为常用基准
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = '2020-01-01'  # 默认加载近3年数据
        
        logger.info(f"预加载沪深300指数数据: {start_date} ~ {end_date}")
        get_index_nav('000300', start_date, end_date, force_update=True)
        logger.info("沪深300指数数据加载完成")
    except Exception as e:
        logger.warning(f"预加载指数数据失败: {str(e)}")

def get_akshare_etf_data(symbol, start, end, cache_dir='etf_cache', force_update=False):
    """
    Fetch ETF data from AkShare with caching support
    
    Args:
        symbol: ETF symbol (e.g., '518880')
        start: Start date in 'YYYY-MM-DD' format
        end: End date in 'YYYY-MM-DD' format
        cache_dir: Directory to store cached data
        force_update: Whether to force update the cache
        
    Returns:
        bt.feeds.PandasData: Backtrader data feed
    """
    os.makedirs(cache_dir, exist_ok=True)
    cache_file = os.path.join(cache_dir, f'{symbol}.pkl')
    start_dt, end_dt = pd.to_datetime(start), pd.to_datetime(end)
    need_download = force_update or (not os.path.exists(cache_file))

    if not need_download:
        try:
            df = pd.read_pickle(cache_file)
            df['date'] = pd.to_datetime(df['日期'])
            # Check if cache covers the required time range
            if df['date'].min() > start_dt or df['date'].max() < end_dt:
                print(f"📌 Cache time range incomplete: {df['date'].min().date()} ~ {df['date'].max().date()}, need to download again")
                need_download = True
        except Exception as e:
            print(f"⚠️ Failed to read cache: {e}")
            need_download = True

    if need_download:
        print(f"⬇️ Downloading ETF data: {symbol}")
        df = ak.fund_etf_hist_em(symbol=symbol)
        if df.empty:
            raise ValueError(f"No data returned from AkShare for symbol {symbol}")
        df['date'] = pd.to_datetime(df['日期'])
        df.to_pickle(cache_file)

    # Filter by date range
    df = df[(df['date'] >= start_dt) & (df['date'] <= end_dt)]
    if df.empty:
        raise ValueError(f"❌ No data available in the specified date range: {start} ~ {end}")

    # Format for backtrader
    df.rename(columns={'date': 'datetime',
                       '开盘': 'open',
                       '最高': 'high',
                       '最低': 'low',
                       '收盘': 'close',
                       '成交量': 'volume'}, inplace=True)
    df = df[['datetime', 'open', 'high', 'low', 'close', 'volume']]
    df['openinterest'] = 0

    data = bt.feeds.PandasData(
        dataname=df,
        datetime='datetime',
        open='open',
        high='high',
        low='low',
        close='close',
        volume='volume',
        openinterest='openinterest',
        name=symbol
    )

    return data

def get_index_nav(symbol, start, end, cache_dir='index_cache', force_update=False):
    """
    Fetch index data from AkShare with caching support
    
    Args:
        symbol: Index symbol (e.g., '000300' for CSI 300)
        start: Start date in 'YYYY-MM-DD' format
        end: End date in 'YYYY-MM-DD' format
        cache_dir: Directory to store cached data
        force_update: Whether to force update the cache
        
    Returns:
        pd.Series: Index NAV series
    """
    os.makedirs(cache_dir, exist_ok=True)
    cache_file = os.path.join(cache_dir, f'{symbol}.pkl')
    start_dt, end_dt = pd.to_datetime(start), pd.to_datetime(end)
    need_download = force_update or (not os.path.exists(cache_file))

    if not need_download:
        try:
            df = pd.read_pickle(cache_file)
            df['date'] = pd.to_datetime(df['日期'])
            # Check if cache covers the required time range
            if df['date'].min() > start_dt or df['date'].max() < end_dt:
                print(f"📌 Cache time range incomplete: {df['date'].min().date()} ~ {df['date'].max().date()}, need to download again")
                need_download = True
        except Exception as e:
            print(f"⚠️ Failed to read cache: {e}")
            need_download = True

    if need_download:
        print(f"⬇️ Downloading index data: {symbol}")
        df = ak.index_zh_a_hist(symbol=symbol, period='daily')
        if df.empty:
            raise ValueError(f"No data returned from AkShare for index {symbol}")
        df['date'] = pd.to_datetime(df['日期'])
        df.to_pickle(cache_file)

    # Filter by date range
    df = df[(df['date'] >= start_dt) & (df['date'] <= end_dt)]
    if df.empty:
        raise ValueError(f"❌ No data available in the specified date range: {start} ~ {end}")

    # Calculate NAV
    df = df.sort_values('date')
    df['nav'] = df['收盘'] / df['收盘'].iloc[0]
    
    return df.set_index('date')['nav']

def get_stock_data(symbol, start, end, cache_dir='stock_cache', force_update=False):
    """
    Fetch stock data from AkShare with caching support
    
    Args:
        symbol: Stock symbol (e.g., '000001')
        start: Start date in 'YYYY-MM-DD' format
        end: End date in 'YYYY-MM-DD' format
        cache_dir: Directory to store cached data
        force_update: Whether to force update the cache
        
    Returns:
        bt.feeds.PandasData: Backtrader data feed
    """
    os.makedirs(cache_dir, exist_ok=True)
    cache_file = os.path.join(cache_dir, f'{symbol}.pkl')
    start_dt, end_dt = pd.to_datetime(start), pd.to_datetime(end)
    need_download = force_update or (not os.path.exists(cache_file))

    if not need_download:
        try:
            df = pd.read_pickle(cache_file)
            df['date'] = pd.to_datetime(df['日期'])
            # Check if cache covers the required time range
            if df['date'].min() > start_dt or df['date'].max() < end_dt:
                logger.info(f"缓存时间范围不完整: {df['date'].min().date()} ~ {df['date'].max().date()}, 需要重新下载")
                need_download = True
        except Exception as e:
            logger.warning(f"读取缓存失败: {e}")
            need_download = True

    if need_download:
        logger.info(f"下载股票数据: {symbol}")
        try:
            # 使用东方财富网数据源
            df = ak.stock_zh_a_hist(symbol=symbol, period="daily", 
                                    start_date=start.replace('-', ''), 
                                    end_date=end.replace('-', ''), 
                                    adjust="qfq")
            if df.empty:
                raise ValueError(f"AkShare未返回股票{symbol}的数据")
            df['date'] = pd.to_datetime(df['日期'])
            df.to_pickle(cache_file)
        except Exception as e:
            logger.error(f"下载股票数据失败: {str(e)}")
            raise

    # Filter by date range
    df = df[(df['date'] >= start_dt) & (df['date'] <= end_dt)]
    if df.empty:
        raise ValueError(f"指定日期范围内没有数据: {start} ~ {end}")

    # Format for backtrader
    df.rename(columns={'date': 'datetime',
                       '开盘': 'open',
                       '最高': 'high',
                       '最低': 'low',
                       '收盘': 'close',
                       '成交量': 'volume'}, inplace=True)
    df = df[['datetime', 'open', 'high', 'low', 'close', 'volume']]
    df['openinterest'] = 0

    data = bt.feeds.PandasData(
        dataname=df,
        datetime='datetime',
        open='open',
        high='high',
        low='low',
        close='close',
        volume='volume',
        openinterest='openinterest',
        name=symbol
    )

    return data