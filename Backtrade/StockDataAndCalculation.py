import pandas as pd
import datetime as dt
import time
from pandas_datareader import data as wb
import os.path
import pytz

home = os.path.expanduser("~")
BT_home = str(home + '/Documents/Backtrade/')


class DATA:

    def __init__(self, *args):
        # print(*args)
        self.StockBunch = {
            "NDX": "NASDAQ100.csv",
            "SPX": "SPX.csv"
        }
        self.tickers = tuple()
        self.data = pd.DataFrame()
        self.buss_day = (dt.datetime.now(pytz.timezone('America/New_York')))
        if len(args) == 1:
            if self.StockBunch.keys().__contains__(*args):
                self.tickers = tuple(pd.read_csv(str(BT_home+'Data/IndexData/'+self.StockBunch[args[0]]), sep=";").keys())
            else:
                self.tickers = args
        else:
            for n in args:
                if self.StockBunch.keys().__contains__(n):
                    self.tickers = (*self.tickers, *tuple(pd.read_csv(str(BT_home+'Data/IndexData/'+self.StockBunch[n]), sep=";").keys()))
                else:
                    self.tickers = (*self.tickers, n)
        self.BussDay()

    def BussDay(self):
        actual_date = (dt.datetime.now(pytz.timezone('America/New_York')))
        if actual_date.weekday() in (5,6):
            self.buss_day=actual_date - dt.timedelta(days=abs(4 - actual_date.weekday()))
        elif actual_date.weekday() in (0,1,2,3,4) and actual_date.time() > dt.time.fromisoformat('09:30'):
            self.buss_day = actual_date
        elif actual_date.weekday() in (1,2,3,4) and actual_date.time() < dt.time.fromisoformat('09:30'):
            self.buss_day = actual_date - dt.timedelta(days=1)
        else:
            self.buss_day = actual_date - dt.timedelta(days=3)
        return

    def ReloadDataFromAV(self):
        data = pd.DataFrame()
        for t in self.tickers:
            if self.CheckValidData(t):
                data = wb.DataReader(t, data_source='av-daily-adjusted', start=None, end=None, api_key='E4RF78ROAZRJNAGK')
                data.index = data.index.rename('date')
                data.to_csv(BT_home+'Data/StockData/' + t + '.csv')
                time.sleep(12)
        return

    def CheckValidData(self, stock):
        if os.path.exists(BT_home+'Data/StockData/' + str(stock) + '.csv'):
            data_pom = pd.read_csv(BT_home+'Data/StockData/' + str(stock) + '.csv', usecols=['date'])['date']
            if dt.datetime.strptime(data_pom.iloc[0], '%Y-%m-%d').date() == self.buss_day.date():
                return False
            else:
                return True
        else:
            return True

    def ReadDataCSV(self):
        for stock in self.tickers:
            data_pom = pd.read_csv(BT_home+'Data/StockData/' + stock + '.csv')
            if self.data.empty:
                data_pom['ticker'] = stock
                data_pom.index = data_pom.index.rename('date')
                self.data = data_pom
                self.data = self.data.reset_index(drop=True)
            else:
                data_pom['ticker'] = stock
                data_pom.index=data_pom.index.rename('date')
                data_pom=data_pom.reset_index(drop=True)
                self.data = self.data.append(data_pom)
                self.data = self.data.reset_index(drop=True)
        self.data = self.data.pivot(index='date', columns='ticker', values=['close', 'open', 'adjusted close', 'dividend amount', 'high', 'low', 'split coefficient', 'volume'])
        return


class Calculation:

    def __init__(self, stockdata):
        self.Data = stockdata

    def Calc_ROC(self, days):
        rocs = pd.DataFrame(index=self.Data.index.copy())
        data_pom = self.Data['close']
        for i in list(data_pom):
            rocs[i] = (data_pom[i].rolling(window=days+1).apply(lambda x: x[-1]-x[0], raw=True)) / data_pom[i].rolling(window=days+1).apply(lambda x: x[0], raw=True)
        return rocs

"""
#Pre Testovanie Prace s datami
skuska = DATA('QQQ','SPY')
skuska.ReloadDataFromAV()
skuska.ReadDataCSV()

#print(skuska.data.head())
Kalkulacie = Calculation(skuska.data)
skuska.data = skuska.data[:-2]
Kalkulacie = Calculation(skuska.data)
#print(skuska.data.tail())

ROC_10 = Kalkulacie.Calc_ROC(10)
ROC_20 = Kalkulacie.Calc_ROC(20)
ROC_60 = Kalkulacie.Calc_ROC(60)
ROC_120 = Kalkulacie.Calc_ROC(120)

Ranking = (ROC_10 + ROC_20 + ROC_60 + ROC_120) / 4
#print(Ranking.iloc[-1])
MoRank = Ranking.ewm(span=60).mean()
#MoScore = MoRank.loc['2018-11-28']
MoScore = MoRank.iloc[-1]
MoScore = MoScore.sort_values(ascending=False)

d_with_len=[d for d in skuska.data if len(d)]
#print(d_with_len)

Tabulka = pd.DataFrame()
Tabulka = MoScore.to_frame(name='MoScore').reset_index()
Tabulka = Tabulka.rename(columns={'index': 'Ticker'})
Tabulka['MoScore'] = Tabulka['MoScore'].round(4) * 100
MA200 = skuska.data['close'].rolling(window=200).mean()

for (index_label, row_series) in Tabulka.iterrows():
    Tabulka.loc[index_label, 'Last_Close'] = skuska.data['close'][Tabulka.loc[index_label, 'Ticker']].iloc[-1]
    Tabulka.loc[index_label, 'MA200'] = MA200[Tabulka.loc[index_label, 'Ticker']].iloc[-1]
Tabulka.to_csv('Tabulka.csv')
#print(Tabulka)
"""
