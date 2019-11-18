import numpy as np
import pandas as pd
import datetime as DT
import time
from pandas_datareader import data as wb
from matplotlib import pyplot as plt

def kontext_filt (doba=200):
    data_kont = pd.DataFrame()
    today = DT.date.today()
    star = today - DT.timedelta(days=doba*2)
    tickers = ['QQQ','SPY','VTWO','OEF']
    for t in tickers:
        data_kont[t] = wb.DataReader(t,data_source = 'av-daily-adjusted', start = star,access_key='E4RF78ROAZRJNAGK' )['close']
        time.sleep(10)
    SMA_20_pom = data_kont.rolling(window=20).mean()
    SMA_200_pom = data_kont.rolling(window=doba).mean()
    index = pd.DataFrame()
    index ['Actual'] = data_kont.iloc[-1]
    index ['SMA_20'] = SMA_20_pom.iloc[-1] 
    index ['SMA_' + str(doba)] = SMA_200_pom.iloc[-1]
    index ['Kontext_20'] = index ['SMA_20'] < index ['Actual'] 
    index ['Kontext_' + str(doba)] = index ['SMA_' + str(doba)] < index ['Actual']
#    index2 = data_kont
#    index2['SMA'] = SMA_200_pom
#    return index2
    return index

def nacitaj_data (symbol = 'NDX',dni=365):
    symbols = {
        "NDX":"NASDAQ100.csv",
        "SPX":"SPX.csv"
    } 
    tickers = pd.read_csv(symbols[symbol], sep = ";")
    tickers = tickers.columns.values.tolist()
#    tickers = ['MELI','CDNS']
    today = DT.date.today()
    star = today - DT.timedelta(days=dni)
    data = pd.DataFrame()
    for t in tickers:
        time.sleep(12)
#        data_pom = wb.DataReader(t,data_source='av-daily-adjusted', start=star,access_key='E4RF78ROAZRJNAGK')
        data_pom = wb.DataReader(t,data_source='av-daily', start=star,access_key='E4RF78ROAZRJNAGK')
        if data.empty:
            data_pom['ticker'] = t
            data_pom.index = data_pom.index.rename('date')
            data = data_pom
            data = data.reset_index()
        else:
            data_pom['ticker'] = t
            data_pom.index = data_pom.index.rename('date')
            data_pom = data_pom.reset_index()
            data = data.append(data_pom)
            data = data.reset_index(drop=True)
#    data = data.pivot(index='date',columns='ticker',values=['close','open','adjusted close','dividend amount','high','low','split coefficient','volume'])
    data = data.pivot(index='date',columns='ticker',values=['close','open','high','low','volume'])        
    return data

def ROC (Price, TF):
    ROC = pd.DataFrame(index=Price.index.copy())
    column = list(Price)
    for i in column:
        ROC[i]=0.0
        x = TF
        while x < (len(Price)):
            rocs = (Price[i][x] - Price[i][x-TF]) / Price[i][x-TF]
            ROC[i][x]=rocs
            x+=1
        
    return ROC

kontext = kontext_filt()
print (kontext)
Akcie = nacitaj_data()
print (Akcie.head())

ROC_10 = ROC (Akcie['close'],10)
ROC_20 = ROC (Akcie['close'],20)
ROC_60 = ROC (Akcie['close'],60)
ROC_120 = ROC (Akcie['close'],120)

Ranking = (ROC_10 + ROC_20 + ROC_60 + ROC_120) / 4
MoRank = Ranking.ewm(span=60)
MoRank = Ranking.ewm(span=60).mean()
MoScore = MoRank.iloc[-2]
MoScore = MoScore.sort_values(ascending = False)

Tabulka = pd.DataFrame()
Tabulka = MoScore.to_frame(name='MoScore').reset_index()
Tabulka = Tabulka.rename(columns = {'index':'Ticker'})
Tabulka['MoScore'] = Tabulka['MoScore']*100
MA200 = Akcie['close'].rolling(window=200).mean()

for (index_label,row_series) in Tabulka.iterrows():
    Tabulka.loc[index_label,'Last_Close']= Akcie['close'][Tabulka.loc[index_label,'Ticker']].iloc[-1]
    Tabulka.loc[index_label,'MA200']= MA200[Tabulka.loc[index_label,'Ticker']].iloc[-1]

print (Tabulka)
