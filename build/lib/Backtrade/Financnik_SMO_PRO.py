from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
import backtrader as bt
import Backtrade.__main__ as main
import pandas as pd
import datetime
import Backtrade.StockDataAndCalculation as SDC
import numpy as np


class IBCommision(bt.CommInfoBase):
    """A :class:`IBCommision` charges the way interactive brokers does.
    """
    params = (
        ('stocklike', True),
        ('commtype', bt.CommInfoBase.COMM_FIXED),
        #('percabs', True),

        # Float. The amount charged per share. Ex: 0.005 means $0.005
        ('per_share', 0.005),

        # Float. The minimum amount that will be charged. Ex: 1.0 means $1.00
        ('min_per_order', 1.0),
        # Float. The maximum that can be charged as a percent of the trade value. Ex: 0.005 means 0.5%
        ('max_per_order_abs_pct', 0.005),
    )

    def _getcommission(self, size, price, pseudoexec):

        """
        :param size: current position size. > 0 for long positions
        and < 0 for short positions (this parameter will not be 0)
        :param price: current position price
        :param pseudoexec:
        :return: the commission of an operation at a given price
        """

        commission = size * self.p.per_share
        order_price = price * size
        commission_as_percentage_of_order_price = commission / order_price

        if commission < self.p.min_per_order:
            commission = self.p.min_per_order
        elif commission_as_percentage_of_order_price > self.p.max_per_order_abs_pct:
            commission = order_price * self.p.max_per_order_abs_pct
        return commission


class Ranking(bt.Indicator):
    lines = ('RO',)
    params = dict(period1=10, period2=20, period3=60, period4=120)

    def __init__(self, dat):

        Var_pom = (bt.talib.ROC(dat, timeperiod=self.params.period1) + bt.talib.ROC(dat, timeperiod=self.params.period2) +
                   bt.talib.ROC(dat, timeperiod=self.params.period3) + bt.talib.ROC(dat, timeperiod=self.params.period4)) / 4
        self.lines.RO = bt.talib.EMA(Var_pom, timeperiod=60)


class TestStrategy(bt.Strategy):
    lines = ('SMA', 'MoScore', 'final')
    params = dict(period_SMA=200, kontext_list=('QQQ',), kontext_data=('AAPL',), kontext_period=200)

    def __init__(self, **kwargs):
        # for arg in kwargs.keys():
        self.last_date = self.datas[2].datetime.date(-1)
        self.logy = pd.DataFrame()
        self.order = None
        self.kontext = self.datas[:len(self.params.kontext_list)]
        self.stocks = self.datas[len(self.params.kontext_list)+1:]

        for d in self.kontext:
            d.lines.SMA = bt.talib.SMA(d.close, timeperiod=self.params.kontext_period)
            d.lines.SMA_comp = d.lines.SMA < d.close
        for i, d in enumerate(self.kontext):
            if i == len(self.kontext)-1:
                break
            else:
                self.konfil = bt.And(self.kontext[i].lines.SMA_comp, self.kontext[i+1].lines.SMA_comp)

        for d in self.stocks:
            d.lines.MoScore = Ranking(dat=d)
            d.lines.SMA = bt.indicators.SimpleMovingAverage(d.close, period=self.params.period_SMA)

    def log(self, txt, stockname=None, ordertype=None, stockprice=None, OrderPrice=None, Comm=None, Size=None, dt=None):
        ' Logging function for this strategy'
        dt = dt or self.datas[0].datetime.date(0)
        if isinstance(dt, float):
            dt = bt.num2date(dt)
        self.logy = self.logy.append({'Date': dt.isoformat(), 'Stock': stockname, 'Order type': ordertype ,'Stock Price': stockprice,
                                      'Order Price': OrderPrice, 'Order Commission': Comm , 'Order Size': Size,'Order': txt, }, ignore_index=True)

    def notify_order(self, order):

        if order.status in [order.Expired]:
            self.log('BUY EXPIRED')

        elif order.status in [order.Completed]:
            if order.isbuy():
                self.log('', order.data._name, 'BUY EXECUTED', order.executed.price, order.executed.value*order.executed.price,
                         order.executed.comm, order.executed.size)
            else:  # Sell
                self.log('', order.data._name,'SELL EXECUTED',order.executed.price,order.executed.value*order.executed.price,
                          order.executed.comm,order.executed.size)

        # Sentinel to None: new orders allowed
        self.order = None
        
    def next(self):
        # Simply log the closing price of the series from the reference
        if self.datas[0].datetime.date(0).isoformat() < '2018-01-01' or self.datas[0].datetime.date(0).isoformat() > '2019-12-01':
            return
        if self.last_date == self.datas[0].datetime.date(0):
            return
        dta = self.datas[0].datetime.date(0)
        Rankings = self.stocks
        Rankings.sort(key=lambda d: float(d.lines.MoScore[0]), reverse=True)
        num_stocks = len(Rankings)

        if (self.datas[0].datetime.date(0).month < self.datas[0].datetime.date(+1).month) or (
                self.datas[0].datetime.date(0).year < self.datas[0].datetime.date(+1).year):
            for d in self.stocks:
                if self.getposition(d).size != 0:
                      self.order = self.close(data=d)
                      self.log('SELL CREATE, %.2f' % d.open[1], d._name)

        if self.konfil[0] and ((self.datas[0].datetime.date(0).month > self.datas[0].datetime.date(-1).month) or (self.datas[0].datetime.date(0).year > self.datas[0].datetime.date(-1).year)):
            for i, d in enumerate(Rankings):
                if i < num_stocks * 0.15 and not np.isnan(d.lines.MoScore[0]):
                    self.log('BUY CREATE, %.2f' % d.close[0], d._name)
                    size_pom = round(self.broker.cash / d.close[0] - 1)*0.1
            # self.order = self.order_target_percent(target=0.5)
                    self.order = self.buy(data=d, size=size_pom, exectype=bt.Order.Market)
                else:
                    break

        if self.order is None:
            if self.konfil[0]:
                for i, d in enumerate(Rankings):
                    if i < num_stocks * 0.15 and not np.isnan(d.lines.MoScore[0]) and self.getposition(data=d).size == 0:
                        self.log('BUY CREATE kontext, %.2f' % d.close[0], d._name)
                        size_pom = round(self.broker.cash / d.close[0] - 1) *0.1
                        # self.order = self.order_target_percent(target=0.99)
                        self.order = self.buy(data=d, size=size_pom, exectype=bt.Order.Market)
                    else:
                        break
            elif not self.konfil[0]:
                for d in self.stocks:
                    if self.getposition(data=d).size != 0:
                        self.log('SELL CREATE kontext, %.2f' % d.open[1], d._name)
                        self.order = self.close(data=d)


def run():
    start = datetime.date(2018, 1, 1)
    cerebro = bt.Cerebro(cheat_on_open=True)
    kontext_list = ('QQQ', 'SPY', )
    stock_list = ('NDX',)
    stock_data = SDC.DATA(*stock_list)
    kontext_data = SDC.DATA(*kontext_list)
    # Reload = input("Do you want to reload data from AV before running test? Y/N: ")
    # if Reload == "Y":
    #     print("reloading")
    #     # kontext_data.ReloadDataFromAV()
    #     # stock_data.ReloadDataFromAV()
    # elif Reload == "N":
    #     print("Not reload")
    # else:
    #     print("wrong input")
    kontext_data.ReadDataCSV()
    kontext_data.data = kontext_data.data[((kontext_data.data.index.get_loc(key=str(start), method='backfill'))-200):-2]
    kontext_data.data.index = pd.to_datetime(kontext_data.data.index)
    for t in kontext_data.data.columns.levels[1]:
        data = kontext_data.data.loc[:,pd.IndexSlice[:, t]]
        data.columns = data.columns.get_level_values(0)
        data_pom = bt.feeds.PandasData(dataname=data)
        cerebro.adddata(data_pom, name=t)

    stock_data.ReadDataCSV()
    stock_data.data.index = pd.to_datetime(stock_data.data.index)
    stock_data.data = stock_data.data[((stock_data.data.index.get_loc(key=str(start), method='backfill'))-200):-2]
    for t in stock_data.tickers:
        data = stock_data.data.loc[:, pd.IndexSlice[:, t]]
        data.columns = data.columns.get_level_values(0)
        data_pom = bt.feeds.PandasData(dataname=data)
        cerebro.adddata(data_pom, name=t)
    kwargs = dict(kontext_list=kontext_list, kontext_data=kontext_data)
    cerebro.addstrategy(TestStrategy, **kwargs)
    cerebro.broker.setcommission(commission=0.005, commtype=bt.CommInfoBase.COMM_FIXED, leverage=2)
    # cerebro.broker.addcommissioninfo(IBCommision(leverage=2))
    cerebro.broker.setcash(40000.0)
    print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='mysharpe')
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='TradeAn')
    cerebro.addanalyzer(bt.analyzers.AnnualReturn, _name='AnnualReturn')
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
    thestrats = cerebro.run()
    thestrat = thestrats[0]
    AnnualReturn = pd.DataFrame.from_dict(thestrat.analyzers.AnnualReturn.get_analysis(),orient='index')
    AnnualReturn.index=AnnualReturn.index.rename('Year')
    AnnualReturn.columns = ['Return']
    AnnualReturn['Return'] *= 100
    AverageReturn = AnnualReturn['Return'].mean()
    print('Sharpe Ratio:', thestrat.analyzers.mysharpe.get_analysis()['sharperatio'])
    print('DrowDown:')
    main.pretty(thestrat.analyzers.drawdown.get_analysis())

    print('TradeAnalyzer:')
    main.pretty (thestrat.analyzers.TradeAn.get_analysis())

    print(AnnualReturn)
    logs = thestrat.logy
    print(thestrat.logy)
    thestrat.logy.to_csv(path_or_buf='logs.csv', index='False')
    print('Average Return: %.2f ' % AverageReturn)
    #print('Trade An:', thestrat.analyzers.TradeAn.get_analysis())
    print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())
    #cerebro.plot()