from __future__ import absolute_import, division, print_function, unicode_literals
import backtrader as bt
import pandas as pd
import numpy as np


class SmoProUpgraded(bt.Strategy):
    lines = ("SMA", "MoScore", "final")
    params = dict(
        period_SMA=200,
        kontext_list=("QQQ",),
        kontext_data=("AAPL",),
        kontext_period=200,
    )

    class Ranking(bt.Indicator):
        lines=("RO",)
        params=dict(period1=10, period2=20, period3=60, period4=120, )

        def __init__(self, dat):
            Var_pom=(
                            bt.talib.ROC(dat, timeperiod=self.params.period1)
                            + bt.talib.ROC(dat, timeperiod=self.params.period2)
                            + bt.talib.ROC(dat, timeperiod=self.params.period3)
                            + bt.talib.ROC(dat, timeperiod=self.params.period4)
                    ) / 4

            self.lines.RO=bt.talib.EMA(Var_pom, timeperiod=60)

    def __init__(self, **kwargs):
        # for arg in kwargs.keys():
        self.last_date = self.datas[2].datetime.date(-1)
        self.logy = pd.DataFrame()
        self.order = None
        self.kontext = self.datas[: len(self.params.kontext_list)]
        self.stocks = self.datas[len(self.params.kontext_list) + 1 :]

        for d in self.kontext:
            d.lines.SMA = bt.talib.SMA(d.close, timeperiod=self.params.kontext_period)
            d.lines.SMA_comp = d.lines.SMA < d.close
        for i, d in enumerate(self.kontext):
            if i == len(self.kontext) - 1:
                break
            else:
                self.konfil = bt.And(
                    self.kontext[i].lines.SMA_comp, self.kontext[i + 1].lines.SMA_comp
                )

        for d in self.stocks:
            d.lines.MoScore = self.Ranking(dat=d)
            d.lines.SMA = bt.indicators.SimpleMovingAverage(
                d.close, period=self.params.period_SMA
            )

    def log(
        self,
        txt,
        stockname=None,
        ordertype=None,
        stockprice=None,
        OrderPrice=None,
        Comm=None,
        Size=None,
        dt=None,
    ):
        " Logging function for this strategy"
        dt = dt or self.datas[0].datetime.date(0)
        if isinstance(dt, float):
            dt = bt.num2date(dt)
        self.logy = self.logy.append(
            {
                "Date": dt.isoformat(),
                "Stock": stockname,
                "Order type": ordertype,
                "Stock Price": stockprice,
                "Order Price": OrderPrice,
                "Order Commission": Comm,
                "Order Size": Size,
                "Order": txt,
            },
            ignore_index=True,
        )

    def notify_order(self, order):
        if order.status in [order.Expired]:
            self.log("BUY EXPIRED")

        elif order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    "",
                    order.data._name,
                    "BUY EXECUTED",
                    order.executed.price,
                    order.executed.value * order.executed.price,
                    order.executed.comm,
                    order.executed.size,
                )
            else:  # Sell
                self.log(
                    "SELL EXECUTED",
                    order.data._name,
                    "SELL EXECUTED",
                    order.executed.price,
                    order.executed.value * order.executed.price,
                    order.executed.comm,
                    order.executed.size,
                )

        # Sentinel to None: new orders allowed
        self.order = None

    """
    def prenext(self):
        # call next() even when data is not available for all tickers
        if self.datas[0].datetime.date(0).isoformat() > "2005-06-01":
            self.next()
        else:
            return
    """
    def next(self):

        if self.datas[0].datetime.date(0).isoformat() < "2005-06-01":
            return
        if self.datas[0].datetime.date(0).isoformat() == "2005-06-01":
            return self.start()
        if self.last_date == self.datas[0].datetime.date(0):
            return self.stop()
        if self.datas[0].datetime.date(0).isoformat() > "2020-01-01":
            return self.stop()

        Rankings = [d for d in self.stocks if not np.isnan(d.lines.MoScore[0])]
        Rankings.sort(key=lambda d: float(d.lines.MoScore[0]), reverse=True)
        num_stocks = len(Rankings)

        if (
            (
                self.datas[0].datetime.date(0).month
                < self.datas[0].datetime.date(+1).month
            )
            or (
                self.datas[0].datetime.date(0).year
                < self.datas[0].datetime.date(+1).year
            )

        ):
            for d in self.stocks:
                if self.getposition(d).size != 0:
                    self.order = self.close(data=d)
                    self.log("SELL CREATE, %.2f" % d.open[1], d._name)

        if self.konfil[0] and (
            (
                self.datas[0].datetime.date(0).month
                > self.datas[0].datetime.date(-1).month
                or self.datas[0].datetime.date(0).year
                > self.datas[0].datetime.date(-1).year
            )

        ):
            for i, d in enumerate(Rankings):
                if i < 15:
                    self.log("BUY CREATE, %.2f" % d.close[0], d._name)
                    size_pom = round((self.broker.cash / d.close[0]) * 0.1)
                    # self.order = self.order_target_percent(target=0.5)
                    self.order = self.buy(
                        data=d, size=size_pom, exectype=bt.Order.Market
                    )
                else:
                    break

        if self.order is None:
            if self.konfil[0]:
                for i, d in enumerate(Rankings):
                    if (
                        i < 15
                        and self.getposition(data=d).size == 0
                    ):
                        self.log("BUY CREATE kontext, %.2f" % d.close[0], d._name)
                        size_pom = round((self.broker.cash / d.close[0]) * 0.1)
                        # self.order = self.order_target_percent(target=0.99)
                        self.order = self.buy(
                            data=d, size=size_pom, exectype=bt.Order.Market
                        )
                    else:
                        break
            elif not self.konfil[0]:
                for d in self.stocks:
                    if self.getposition(data=d).size != 0:
                        self.log("SELL CREATE kontext, %.2f" % d.open[1], d._name)
                        self.order = self.close(data=d)
