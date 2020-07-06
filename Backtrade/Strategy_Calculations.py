import pandas as pd
import datetime as dt
import time
from pandas_datareader import data as wb
import os.path
import pytz
import sys
import talib
import numpy as np
import datetime
import inspect
import csv

home = os.path.expanduser("~")
BT_home = str(home + "/Documents/Backtrade/")
sysdate = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M")


def BussDay(actual_date=dt.datetime.now(pytz.timezone("America/New_York"))):
    if actual_date.weekday() in (5, 6):
        buss_day = actual_date - dt.timedelta(days=abs(4 - actual_date.weekday()))
    elif actual_date.weekday() in (
        0,
        1,
        2,
        3,
        4,
    ) and actual_date.time() > dt.time.fromisoformat("09:30"):
        buss_day = actual_date
    elif actual_date.weekday() in (
        1,
        2,
        3,
        4,
    ) and actual_date.time() < dt.time.fromisoformat("09:30"):
        buss_day = actual_date - dt.timedelta(days=1)
    else:
        buss_day = actual_date - dt.timedelta(days=3)
    return buss_day


def progressbar(dat, prefix="", count=1, size=60, file=sys.stdout):
    percent = dat / count
    x = int(size * percent)

    print(
        "%s[%s%s] %.2f %%\r" % (prefix, "#" * x, "." * (size - x), percent * 100),
        flush=True,
    )


def kontext_filt(st_date=BussDay(), doba=200, *args):
    data_kont = pd.DataFrame()
    st_date = st_date - dt.timedelta(days=doba*2)
    if args:
        tickers = args
    else:
        tickers = ['QQQ', 'SPY']

    data_kont = DATA(*tickers)
    data_kont.ReloadDataFromAV()
    data_kont.ReadDataCSV()

    data_kont = data_kont.data["close"]
    print(data_kont)

    sma_20_pom=data_kont.rolling(window=20).mean()
    sma_doba_pom=data_kont.rolling(window=doba).mean()
    print(sma_doba_pom.tail())
    # for stock in tickers:
        
    index2 = (sma_doba_pom['QQQ'] < data_kont['QQQ']) & (sma_doba_pom['SPY'] < data_kont['SPY'])
    print("\n", index2)
    print("\n", index2.loc["2020-02-04"])
    """
    index=pd.DataFrame()
    index['Actual']=data_kont.iloc[-1]
    index['SMA_20']=sma_20_pom.iloc[-1]
    index['SMA_' + str(doba)]=sma_doba_pom.iloc[-1]
    index['Kontext_20']=index['SMA_20'] < index['Actual']
    index['Kontext_' + str(doba)]=index['SMA_' + str(doba)] < index['Actual']
    index['Kontext_200_last_5']=(sma_doba_pom.iloc[-1] < index['Actual']) & (sma_doba_pom.iloc[-2] < index['Actual']) & \
                                (sma_doba_pom.iloc[-3] < index['Actual']) & (sma_doba_pom.iloc[-4] < index['Actual']) & \
                                (sma_doba_pom.iloc[-5] < index['Actual'])
    """
    return index2


class DATA:
    def __init__(self, *args):
        self.StockBunch = {"NDX": "NASDAQ100.csv", "SPX": "SPY500.csv"}
        self.tickers = tuple()
        self.data = pd.DataFrame()
        self.buss_day = dt.datetime.now(pytz.timezone("America/New_York"))
        if len(args) == 1:
            if self.StockBunch.keys().__contains__(*args):
                self.tickers = tuple(
                    pd.read_csv(
                        str(BT_home + "Data/IndexData/" + self.StockBunch[args[0]]),
                        sep=";",
                    ).keys()
                )
            else:
                self.tickers = args
        else:
            for n in args:
                if self.StockBunch.keys().__contains__(n):
                    self.tickers = (
                        *self.tickers,
                        *tuple(
                            pd.read_csv(
                                str(BT_home + "Data/IndexData/" + self.StockBunch[n]),
                                sep=";",
                            ).keys()
                        ),
                    )
                else:
                    self.tickers = (*self.tickers, n)
        self.buss_day = BussDay()

    def ReloadDataFromAV(self):
        data = pd.DataFrame()
        progressbar(0, "Computing: ", len(self.tickers))
        for t in self.tickers:
            if self.CheckValidData(t):
                data = wb.DataReader(
                    t,
                    data_source="av-daily-adjusted",
                    start=None,
                    end=None,
                    api_key="E4RF78ROAZRJNAGK",
                )
                data.index = data.index.rename("date")
                data.to_csv(BT_home + "Data/StockData/" + t + ".csv")
                time.sleep(12)
            progressbar(
                self.tickers.index(t) + 1, "Computing: ", len(self.tickers)
            )
        return

    def CheckValidData(self, stock):
        if os.path.exists(BT_home + "Data/StockData/" + str(stock) + ".csv"):
            data_pom = pd.read_csv(
                BT_home + "Data/StockData/" + str(stock) + ".csv", usecols=["date"]
            )["date"]
            if (
                dt.datetime.strptime(data_pom.iloc[-1], "%Y-%m-%d").date()
                == self.buss_day.date()
            ):
                return False
            else:
                return True
        else:
            return True

    def ReadDataCSV(self):
        for stock in self.tickers:
            data_pom = pd.read_csv(BT_home + "Data/StockData/" + stock + ".csv")
            if self.data.empty:
                data_pom["ticker"] = stock
                data_pom.index = data_pom.index.rename("date")
                self.data = data_pom
                self.data = self.data.reset_index(drop=True)
            else:
                data_pom["ticker"] = stock
                data_pom.index = data_pom.index.rename("date")
                data_pom = data_pom.reset_index(drop=True)
                self.data = self.data.append(data_pom)
                self.data = self.data.reset_index(drop=True)
        self.data = self.data.pivot(
            index="date",
            columns="ticker",
            values=[
                "close",
                "open",
                "adjusted close",
                "dividend amount",
                "high",
                "low",
                "split coefficient",
                "volume",
            ],
        )
        self.data = self.data.fillna(method="backfill")
        self.data = self.data.fillna(method="ffill")
        self.data = self.data.fillna(value=0)
        return


class Calculation:
    def __init__(self, stockdata):
        self.Data = stockdata

    def Calc_ROC(self, days):
        rocs = pd.DataFrame(index=self.Data.index.copy())
        data_pom = self.Data["close"]
        for i in list(data_pom):
            rocs[i] = talib.ROC(data_pom[i], days)
        return rocs


class StrategieCalculations:
    def __init__(self, stockdata):
        self.data = stockdata
        self.csv_name = str()

    def CreateCSV(self, date):
        caller_name = inspect.stack()[1][3]
        strdate = date.strftime("%Y-%m-%d")
        self.csv_name = str(
            BT_home + "Calculated_Tables/" + caller_name + "_" + strdate + ".csv"
        )
        with open(self.csv_name, "w+", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["Strategy:", caller_name])
            writer.writerow(["Calculated for date:", strdate])

    def SmoProUpgraded(self, date=BussDay(), port_value=40000, stock_num=15):
        kalkulacie = Calculation(self.data)
        roc_10 = kalkulacie.Calc_ROC(10)
        roc_20 = kalkulacie.Calc_ROC(20)
        roc_60 = kalkulacie.Calc_ROC(60)
        roc_120 = kalkulacie.Calc_ROC(120)

        ranking = (roc_10 + roc_20 + roc_60 + roc_120) / 4
        mo_rank = ranking.ewm(span=60).mean() / 100
        mo_score = mo_rank.iloc[-1]
        mo_score = mo_score.sort_values(ascending=False)

        calculated_table = mo_score.to_frame(name="MoScore").reset_index()
        calculated_table = calculated_table.rename(columns={"index": "Ticker"})
        calculated_table["MoScore"] = calculated_table["MoScore"].round(4) * 100
        ma_200 = self.data["close"].rolling(window=200).mean()
        ma_200_ok = self.data["close"] > ma_200

        for (index_label, row_series) in calculated_table.iterrows():
            calculated_table.loc[index_label, "Last_Close"] = self.data["close"][
                calculated_table.loc[index_label, "Ticker"]
            ].iloc[-1]
            calculated_table.loc[index_label, "MA200"] = ma_200[
                calculated_table.loc[index_label, "Ticker"]
            ].iloc[-1]
            calculated_table.loc[index_label, "MA200_OK"] = (
                ma_200_ok[calculated_table.loc[index_label, "Ticker"]]
                .iloc[-1]
                .astype(bool)
            )
            calculated_table.loc[index_label, "MoScore"] = (
                calculated_table.loc[index_label, "MoScore"]
                if calculated_table.loc[index_label, "MA200_OK"]
                else "0"
            )

        stock_above_score = len(
            calculated_table[calculated_table["MoScore"].astype(float) > 0].index
        )
        stock_num = stock_above_score if stock_above_score < stock_num else stock_num
        one_stock_value = port_value / stock_num

        for (index_label, row_series) in calculated_table.iterrows():
            if stock_num > 0:
                calculated_table.loc[index_label, "stock number"] = round(
                    one_stock_value
                    / self.data["close"][
                        calculated_table.loc[index_label, "Ticker"]
                    ].iloc[-1]
                )
                stock_num -= 1
            else:
                calculated_table.loc[index_label, "stock number"] = 0

        self.CreateCSV(date)
        calculated_table.to_csv(path_or_buf=self.csv_name, mode="a", index=False)
