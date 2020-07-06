from __future__ import absolute_import, division, print_function, unicode_literals
import backtrader as bt
import Backtrade.__main__ as main
import pandas as pd
import datetime
import Backtrade.Strategy_Calculations as SDC
import Backtrade.BTSetup as BTSetup
import Backtrade.Strategies as Strategies


def run():
    start = datetime.date(2002, 1, 1)
    cerebro = bt.Cerebro(cheat_on_open=False)
    kontext_list = (
        "QQQ",
        "SPY",
    )
    stock_list = ("AAPL", "FB", )
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
    kontext_data.data = kontext_data.data[
        (
            (kontext_data.data.index.get_loc(key=str(start), method="backfill")) - 200
        ) : -2
    ]
    kontext_data.data.index = pd.to_datetime(kontext_data.data.index)
    for t in kontext_data.data.columns.levels[1]:
        data = kontext_data.data.loc[:, pd.IndexSlice[:, t]]
        data.columns = data.columns.get_level_values(0)
        data = data.reset_index()
        data_pom = BTSetup.PData(dataname=data)
        """
        data_pom = CSVData(
            dataname=(SDC.BT_home + "Data/StockData/" + t + ".csv"),
            timeframe=bt.TimeFrame.Days,
            compression=1,
            fromdate=start,
        )"""
        cerebro.adddata(data_pom, name=t)

    stock_data.ReadDataCSV()
    stock_data.data.index = pd.to_datetime(stock_data.data.index)
    stock_data.data = stock_data.data[
        ((stock_data.data.index.get_loc(key=str(start), method="backfill")) - 200) : -2
    ]
    stock_data.data = stock_data.data.fillna(method="bfill")

    for t in stock_data.tickers:
        data = stock_data.data.loc[:, pd.IndexSlice[:, t]]
        data.columns = data.columns.get_level_values(0)
        data = data.reset_index()
        data = data.fillna(method="bfill")
        data_pom = BTSetup.PData(dataname=data)
        """
        data_pom = CSVData(
            dataname=(SDC.BT_home + "Data/StockData/" + t + ".csv"),
            timeframe=bt.TimeFrame.Days,
            compression=1,
            fromdate=start,
        )"""
        cerebro.adddata(data_pom, name=t)
    kwargs = dict(kontext_list=kontext_list, kontext_data=kontext_data)
    cerebro.addstrategy(Strategies.SmoProUpgraded, **kwargs)
    cerebro.broker.setcommission(
        commission=0.005, commtype=bt.CommInfoBase.COMM_FIXED, leverage=2
    )
    # cerebro.broker.addcommissioninfo(IBCommision(leverage=2))
    cerebro.broker.setcash(40000.0)
    print("Starting Portfolio Value: %.2f" % cerebro.broker.getvalue())
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name="mysharpe")
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name="TradeAn")
    cerebro.addanalyzer(bt.analyzers.AnnualReturn, _name="AnnualReturn")
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name="drawdown")
    cerebro.addanalyzer(BTSetup.trade_list, _name="trade_list")
    thestrats = dict
    thestrats = cerebro.run(tradehistory=True)
    thestrat = thestrats[0]
    AnnualReturn = pd.DataFrame.from_dict(
        thestrat.analyzers.AnnualReturn.get_analysis(), orient="index"
    )

    AnnualReturn.index = AnnualReturn.index.rename("Year")
    AnnualReturn.columns = ["Return"]
    AnnualReturn["Return"] *= 100
    AverageReturn = AnnualReturn["Return"].mean()
    print("Sharpe Ratio:", thestrat.analyzers.mysharpe.get_analysis()["sharperatio"])
    print("DrowDown:")
    main.pretty(thestrat.analyzers.drawdown.get_analysis())

    print("TradeAnalyzer:")
    main.pretty(thestrat.analyzers.TradeAn.get_analysis())

    print(AnnualReturn)
    sysdate = str(datetime.datetime.now().strftime("%Y-%m-%d_%H-%M"))
    thestrat.logy.to_csv(path_or_buf="./Data/Logs/logs_"+sysdate+".csv", index="False")
    print("Average Return: %.2f " % AverageReturn)
    # print('Trade An:', thestrat.analyzers.TradeAn.get_analysis())
    print("Final Portfolio Value: %.2f" % cerebro.broker.getvalue())
    trade_list = thestrats[0].analyzers.trade_list.get_analysis()
    trade_df = pd.DataFrame(trade_list)
    trade_df.to_csv(path_or_buf="./Data/Logs/Trade_logs/trade_logs_"+sysdate+".csv", index="False")
    # cerebro.plot()
