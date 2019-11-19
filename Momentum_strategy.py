from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
import backtrader as bt
import main
import pandas as pd
import datetime

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

class TestStrategy(bt.Strategy):

    def log(self, txt, stockname=None, ordertype=None, stockprice=None, OrderPrice=None, Comm=None, Size=None, dt=None):
        ' Logging function for this strategy'
        dt = dt or self.datas[0].datetime.date(0)
        if isinstance(dt, float):
            dt = bt.num2date(dt)
        #print('%s, %s' % (dt.isoformat(), txt))
        self.logy = self.logy.append({'Date': dt.isoformat(), 'Stock': stockname, 'Order type': ordertype ,'Stock Price': stockprice,
                                      'Order Price': OrderPrice, 'Order Commission': Comm , 'Order Size': Size,'Order': txt, }, ignore_index=True)

    def __init__(self):
        # Keep a reference to the "close" line in the data[0] dataseries
        self.dataclose = self.datas[0].close
        self.last_date = self.datas[0].datetime.date(-1)
        self.logy = pd.DataFrame()
        self.order = None

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
        if self.datas[0].datetime.date(0).isoformat() < '2004-01-01':
            return
        dta = self.datas[0].datetime.date(0)
        for d in self.datas:  
          
            if self.last_date > self.datas[0].datetime.date(0):
                if (self.datas[0].datetime.date(0).month < self.datas[0].datetime.date(+1).month) or (self.datas[0].datetime.date(0).year < self.datas[0].datetime.date(+1).year):
                    if (self.getposition(d).size) != 0:
                        self.order = self.close(data=d)
                        self.log('SELL CREATE, %.2f' % d.open[1],d._name)
                        cerebro.broker.cash += 1000
            #    if (kontext.loc[dta.isoformat()]) and ((self.datas[0].datetime.date(0).month > self.datas[0].datetime.date(-1).month) or (self.datas[0].datetime.date(0).year > self.datas[0].datetime.date(-1).year)):
            # current close less than previous close
            #        self.log('BUY CREATE, %.2f' % self.datas[1].close[0],self.datas[1]._name)
            #        size_pom = round(cerebro.broker.cash / self.datas[1].close[0] -1)*1.5
            #        #self.order = self.order_target_percent(target=0.5)
            #        self.order = self.buy(data=self.datas[1],size=size_pom,exectype=bt.Order.Market)
        
        if self.order == None:
            if (kontext.loc[dta.isoformat()]) and (self.getposition(data=self.datas[1]).size == 0):
            # current close less than previous close
                self.log('BUY CREATE kontext, %.2f' % self.datas[1].open[1],self.datas[1]._name)
                size_pom = round(cerebro.broker.cash / self.datas[1].close[0] -1) *1.5
                    #self.order = self.order_target_percent(target=0.99)
                self.order = self.buy(data=self.datas[1],size=size_pom,exectype=bt.Order.Market)
                if self.getposition(data=self.datas[0]).size != 0:
                    self.order = self.close(data=self.datas[0])
                    self.log('SELL CREATE, %.2f' % self.datas[0].open[1],self.datas[0]._name)    
            elif (self.getposition(data=self.datas[1]).size != 0) and ((kontext.loc[dta.isoformat()]) == False):
                self.log('SELL CREATE kontext, %.2f' % self.datas[1].open[1],self.datas[1]._name)
                self.order = self.close(data=self.datas[1])
                if self.getposition(data=self.datas[0]).size == 0:
                    size_pom = round(cerebro.broker.cash / self.datas[0].close[0] -1) *1.5
                    self.order = self.buy(data=self.datas[0],size=size_pom,exectype=bt.Order.Market)
                    self.log('BUY CREATE, %.2f' % self.datas[0].open[1],self.datas[0]._name)    
                
     
start= datetime.date(2000, 1, 1)
cerebro = bt.Cerebro(cheat_on_open=True)
kontext = main.kontext_filt(st_date = start, doba=200)
kontext.index = pd.to_datetime(kontext.index)
#print (kontext)
Akcie = main.nacitaj_data(st_date = start)
#print (Akcie.head())
idx = pd.IndexSlice
#print (Akcie.loc[idx[:],idx[:, 'GLD']])
Akcie.index = pd.to_datetime(Akcie.index)
Akcie = Akcie.dropna()
for t in Akcie.columns.levels[1]:
    data = Akcie.loc[idx[:],idx[:, t]]
    data.columns = data.columns.get_level_values(0)
#print (data.head())
    data_pom = bt.feeds.PandasData(dataname=data)
    cerebro.adddata(data_pom,name=t)
cerebro.addstrategy(TestStrategy)
cerebro.broker.setcommission(commission=0.005,commtype = bt.CommInfoBase.COMM_FIXED,leverage=2)
#cerebro.broker.addcommissioninfo(IBCommision)
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
AnnualReturn['Return'] *=100
AverageReturn = AnnualReturn['Return'].mean() 
print('Sharpe Ratio:', thestrat.analyzers.mysharpe.get_analysis()['sharperatio'])
print('DrowDown:')
main.pretty(thestrat.analyzers.drawdown.get_analysis())

print('TradeAnalyzer:')
main.pretty (thestrat.analyzers.TradeAn.get_analysis())

print(AnnualReturn)
logs = thestrat.logy
#print (thestrat.logy)
print('Average Return: %.2f ' % AverageReturn)
#print('Trade An:', thestrat.analyzers.TradeAn.get_analysis())
print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())
cerebro.plot()
