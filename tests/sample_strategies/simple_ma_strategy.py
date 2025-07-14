#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
简单移动平均线策略示例

这个策略使用两条移动平均线（快线和慢线）来生成交易信号：
- 当快线上穿慢线时买入
- 当快线下穿慢线时卖出
"""

import backtrader as bt


class SimpleMAStrategy(bt.Strategy):
    """
    简单双均线策略
    """
    
    params = (
        ('fast_period', 10),  # 快速均线周期
        ('slow_period', 30),  # 慢速均线周期
        ('printlog', False),  # 是否打印日志
    )
    
    def __init__(self):
        """初始化策略"""
        # 保存收盘价的引用
        self.dataclose = self.datas[0].close
        
        # 跟踪挂单、持仓和交易次数
        self.order = None
        self.buyprice = None
        self.buycomm = None
        self._tradeid = 0
        
        # 添加移动平均线指标
        self.fast_ma = bt.indicators.SMA(
            self.datas[0], period=self.params.fast_period
        )
        self.slow_ma = bt.indicators.SMA(
            self.datas[0], period=self.params.slow_period
        )
        
        # 添加交叉指标
        self.crossover = bt.indicators.CrossOver(self.fast_ma, self.slow_ma)
        
        # 用于存储每日净值的列表
        self.navs = []
    
    def log(self, txt, dt=None, doprint=False):
        """记录策略日志"""
        if self.params.printlog or doprint:
            dt = dt or self.datas[0].datetime.date(0)
            print(f'{dt.isoformat()} {txt}')
    
    def notify_order(self, order):
        """处理订单状态变化"""
        if order.status in [order.Submitted, order.Accepted]:
            # 订单已提交/已接受 - 无需操作
            return
        
        # 检查订单是否已完成
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    f'买入执行: 价格: {order.executed.price:.2f}, '
                    f'成本: {order.executed.value:.2f}, '
                    f'手续费: {order.executed.comm:.2f}'
                )
                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            else:  # 卖出
                self.log(
                    f'卖出执行: 价格: {order.executed.price:.2f}, '
                    f'成本: {order.executed.value:.2f}, '
                    f'手续费: {order.executed.comm:.2f}'
                )
            
            self._tradeid += 1
        
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('订单取消/保证金不足/拒绝')
        
        # 重置订单变量
        self.order = None
    
    def notify_trade(self, trade):
        """处理交易状态变化"""
        if not trade.isclosed:
            return
        
        self.log(f'交易利润, 毛利润: {trade.pnl:.2f}, 净利润: {trade.pnlcomm:.2f}')
    
    def next(self):
        """每个bar执行一次"""
        # 记录当前净值
        self.navs.append(self.broker.getvalue())
        
        # 如果有挂单，不执行新的交易
        if self.order:
            return
        
        # 检查是否持仓
        if not self.position:
            # 如果没有持仓，检查是否有买入信号
            if self.crossover > 0:  # 快线上穿慢线
                self.log(f'买入信号, 收盘价: {self.dataclose[0]:.2f}')
                # 买入
                self.order = self.buy()
        
        else:
            # 如果已经持仓，检查是否有卖出信号
            if self.crossover < 0:  # 快线下穿慢线
                self.log(f'卖出信号, 收盘价: {self.dataclose[0]:.2f}')
                # 卖出
                self.order = self.sell()
    
    def stop(self):
        """策略结束时执行"""
        self.log('(快速均线周期 %2d) (慢速均线周期 %2d) 最终资金: %.2f' %
                 (self.params.fast_period, self.params.slow_period, self.broker.getvalue()), 
                 doprint=True)