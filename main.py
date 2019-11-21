import numpy as np
import pandas as pd
import datetime as DT
import time
import datetime
from pandas_datareader import data as wb
from matplotlib import pyplot as plt


def kontext_filt(st_date=datetime.date(2017, 1, 1), doba=200):
    data_kont = pd.DataFrame()
    data_pom = pd.DataFrame()
    # st_date = st_date - DT.timedelta(days=doba*2)
    tickers = ['QQQ', 'SPY', 'VTWO', 'OEF']
    
    for t in tickers:
        data_pom = pd.read_csv('Data/'+t+'.csv',usecols=['date', 'adjusted close'])
        if data_kont.empty:
            data_pom = data_pom.set_index('date')
            data_pom = data_pom.rename(columns={'adjusted close': t})
            data_kont = data_pom
        else:
            data_pom = data_pom.set_index('date')
            data_pom = data_pom.rename(columns={'adjusted close': t})
            data_kont = pd.merge(data_kont, data_pom, on='date', how='outer')
    '''
    for t in tickers:
        data_kont[t] = wb.DataReader(t,data_source = 'av-daily-adjusted', start = st_date,access_key='E4RF78ROAZRJNAGK')['adjusted close']
        time.sleep(10)
    '''
    data_kont.to_csv(path_or_buf='data1.csv', index='False')
    sma_20_pom = data_kont.rolling(window=20).mean()
    sma_doba_pom = data_kont.rolling(window=doba).mean()
    index2 = (sma_doba_pom['QQQ'] < data_kont['QQQ']) & (sma_doba_pom['SPY'] < data_kont['SPY'])
    index = pd.DataFrame()
    index['Actual'] = data_kont.iloc[-1]
    index['SMA_20'] = sma_20_pom.iloc[-1]
    index['SMA_' + str(doba)] = sma_doba_pom.iloc[-1]
    index['Kontext_20'] = index['SMA_20'] < index['Actual']
    index['Kontext_' + str(doba)] = index['SMA_' + str(doba)] < index['Actual']
    index['Kontext_200_last_5'] = (sma_doba_pom.iloc[-1] < index['Actual']) & (sma_doba_pom.iloc[-2] < index['Actual']) & \
                                   (sma_doba_pom.iloc[-3] < index['Actual']) & (sma_doba_pom.iloc[-4] < index['Actual']) & \
                                   (sma_doba_pom.iloc[-5] < index['Actual'])
    return index2


def nacitaj_data(symbol='NDX', st_date=datetime.date(2017, 1, 1)):
    # tickers = tickers.columns.values.tolist()
    tickers = ['QQQ', 'GLD']
    data = pd.DataFrame()
    for t in tickers:
        # time.sleep(12)
        data_pom = pd.read_csv('Data/'+t+'.csv')
        if data.empty:
            data_pom['ticker'] = t
            data_pom.index = data_pom.index.rename('date')
            data = data_pom
            data = data.reset_index(drop=True)
        else:
            data_pom['ticker'] = t
            data_pom.index = data_pom.index.rename('date')
            data_pom = data_pom.reset_index(drop=True)
            data = data.append(data_pom)
            data = data.reset_index(drop=True)
    data = data.pivot(index='date', columns='ticker', values=['close', 'open', 'adjusted close', 'dividend amount',
                                                              'high', 'low', 'split coefficient', 'volume'])
    return data


def pretty(d, indent=0):
    for key, value in d.items():
        print('\t' * indent + str(key),end='')
        if isinstance(value, dict):
            print('')
            pretty(value, indent+1)
        else:
            print(': '+str(value))
