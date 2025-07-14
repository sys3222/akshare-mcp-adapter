import backtrader as bt
import numpy as np
import math

class ETFMomentumStrategy(bt.Strategy):
    """
    ETF Momentum Strategy that selects the best performing ETF based on momentum score
    """
    params = dict(
        m_days=25,  # Lookback period for momentum calculation
        printlog=True,
        commission=0.0002,
        slippage=0.000,
    )

    def __init__(self):
        # Store data feeds by name
        self.etf_data = {d._name: d for d in self.datas}
        self.order_list = []
        self.navs = []  # Store NAV values for each bar

    def log(self, txt, dt=None):
        """Logging function"""
        if not self.params.printlog:
            return
        dt = dt or self.datas[0].datetime.date(0)
        print(f'{dt.isoformat()}, {txt}')

    def notify_order(self, order):
        """Order notification"""
        if order.status in [order.Completed]:
            self.log(f'ORDER EXECUTED, {order.data._name}, {order.executed.price:.2f}')
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log(f'ORDER FAILED, {order.data._name}, Status: {order.Status[order.status]}')

    def get_rank(self):
        """Calculate momentum scores and rank ETFs"""
        scores = {}
        for name, d in self.etf_data.items():
            closes = d.close.get(size=self.params.m_days)
            if len(closes) < self.params.m_days:
                continue
            
            # Calculate momentum score using log returns and linear regression
            log_prices = np.log(closes)
            x = np.arange(len(log_prices))
            slope, intercept = np.polyfit(x, log_prices, 1)
            
            # Calculate R-squared
            y_pred = slope * x + intercept
            r2 = 1 - np.sum((log_prices - y_pred) ** 2) / ((len(log_prices) - 1) * np.var(log_prices, ddof=1))
            
            # Annualized return
            ann_return = math.pow(math.exp(slope), 250) - 1
            
            # Final score is annualized return * R-squared
            score = ann_return * r2
            scores[name] = score
            
        # Sort by score in descending order
        sorted_etfs = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return [etf[0] for etf in sorted_etfs]

    def next(self):
        """Main strategy logic executed on each bar"""
        # Store current portfolio value
        self.navs.append(self.broker.getvalue())

        # Get ETF rankings
        rank = self.get_rank()
        if not rank:
            return

        # Select top ETF
        target = rank[0]

        # Sell all ETFs except the target
        for etf in self.etf_data:
            pos = self.getposition(self.etf_data[etf])
            if pos.size > 0 and etf != target:
                self.order_target_percent(self.etf_data[etf], target=0.0)
                self.log(f'Selling {etf}')

        # Buy the target ETF if not already holding it
        current_pos = self.getposition(self.etf_data[target])
        if current_pos.size == 0:
            value = self.broker.getcash()
            price = self.etf_data[target].close[0]
            self.log(f'{target} current price: {price:.2f}, cash: {value:.2f}')
            self.order_target_value(self.etf_data[target], target=value * 0.99)
            self.log(f'Buying {target} amount: {value * 0.99:.2f}')
        else:
            self.log(f'Holding {target}')

    def stop(self):
        """Called when strategy is done"""
        self.log(f'Final Portfolio Value: {self.broker.getvalue():.2f}')