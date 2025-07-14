import backtrader as bt

class SampleStrategy(bt.Strategy):
    """
    A simple moving average crossover strategy
    """
    params = (
        ('fast_period', 10),
        ('slow_period', 30),
    )
    
    def __init__(self):
        # Initialize indicators
        self.fast_ma = bt.indicators.SMA(self.data.close, period=self.params.fast_period)
        self.slow_ma = bt.indicators.SMA(self.data.close, period=self.params.slow_period)
        self.crossover = bt.indicators.CrossOver(self.fast_ma, self.slow_ma)
        
        # Initialize trade counter
        self._tradeid = 0
    
    def next(self):
        # Check for buy signal
        if self.crossover > 0:  # Fast MA crosses above slow MA
            self.buy()
            self._tradeid += 1
        
        # Check for sell signal
        elif self.crossover < 0:  # Fast MA crosses below slow MA
            self.sell()
            self._tradeid += 1