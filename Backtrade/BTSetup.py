import backtrader as bt


class CSVData(bt.feeds.GenericCSVData):
    params = (
        # ("nullvalue", float(0)),
        ("dtformat", ("%Y-%m-%d")),
        ("datetime", 0),
        ("high", 2),
        ("low", 3),
        ("open", 1),
        ("close", 4),
        ("volume", 6),
    )


class PData(bt.feeds.PandasData):
    params = (
        # ("nullvalue", float(0)),
        ("dtformat", ("%Y-%m-%d")),
        ("datetime", 0),
        ("high", 5),
        ("low", 6),
        ("open", 2),
        ("close", 1),
        ("volume", 8),
    )


class IBCommision(bt.CommInfoBase):
    """A :class:`IBCommision` charges the way interactive brokers does.
    """

    params = (
        ("stocklike", True),
        ("commtype", bt.CommInfoBase.COMM_FIXED),
        # ('percabs', True),
        # Float. The amount charged per share. Ex: 0.005 means $0.005
        ("per_share", 0.005),
        # Float. The minimum amount that will be charged. Ex: 1.0 means $1.00
        ("min_per_order", 1.0),
        # Float. The maximum that can be charged as a percent of the trade value. Ex: 0.005 means 0.5%
        ("max_per_order_abs_pct", 0.005),
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


class trade_list(bt.Analyzer):

    def get_analysis(self):

        return self.trades


    def __init__(self):

        self.trades = []
        self.cumprofit = 0.0


    def notify_trade(self, trade):

        if trade.isclosed:

            brokervalue = self.strategy.broker.getvalue()

            dir = 'short'
            if trade.history[0].event.size > 0: dir = 'long'

            pricein = trade.history[len(trade.history)-1].status.price
            priceout = trade.history[len(trade.history)-1].event.price
            datein = bt.num2date(trade.history[0].status.dt)
            dateout = bt.num2date(trade.history[len(trade.history)-1].status.dt)
            if trade.data._timeframe >= bt.TimeFrame.Days:
                datein = datein.date()
                dateout = dateout.date()

            pcntchange = 100 * priceout / pricein - 100
            pnl = trade.history[len(trade.history)-1].status.pnlcomm
            pnlpcnt = 100 * pnl / brokervalue
            barlen = trade.history[len(trade.history)-1].status.barlen
            pbar = pnl / barlen
            self.cumprofit += pnl

            size = value = 0.0
            for record in trade.history:
                if abs(size) < abs(record.status.size):
                    size = record.status.size
                    value = record.status.value * pricein

            highest_in_trade = max(trade.data.high.get(ago=0, size=barlen+1))
            lowest_in_trade = min(trade.data.low.get(ago=0, size=barlen+1))
            hp = 100 * (highest_in_trade - pricein) / pricein
            lp = 100 * (lowest_in_trade - pricein) / pricein
            if dir == 'long':
                mfe = hp
                mae = lp
            if dir == 'short':
                mfe = -lp
                mae = -hp

            self.trades.append({'ref': trade.ref, 'ticker': trade.data._name, 'dir': dir,
                 'datein': datein, 'pricein': pricein, 'dateout': dateout, 'priceout': priceout,
                 'chng%': round(pcntchange, 2), 'pnl': pnl, 'pnl%': round(pnlpcnt, 2),
                 'size': size, 'value': value, 'cumpnl': self.cumprofit,
                 'nbars': barlen,
                 'pnl/bar': round(pbar, 2),
                 'mfe%': round(mfe, 2), 'mae%': round(mae, 2)})