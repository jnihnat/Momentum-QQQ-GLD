import pandas as pd
import numpy as np
import quandl

quandl.ApiConfig.api_key = 'pYVNssUuYhxojhZk46Hy'
data = quandl.get_table('WIKI/PRICES', 
                        qopts = { 'columns': ['ticker', 'date', 'close', 'open'] }, 
                        ticker = ['AAPL', 'MSFT'], 
                        date = { 'gte': '2016-01-01', 'lte': '2016-12-31' })
print (data)
data = data.pivot(index='date', columns = 'ticker',values = ['close','open'])
print (data)
close = data['close']
tickers = ['AAPL','MSFT']
returns = close / close.shift(1) / 1


returns.columns = pd.MultiIndex.from_product([returns.columns, ['returns']])
returns = returns.swaplevel(i=-2, j=-1, axis=1)
data2 = data.join(returns,rsuffix='_ret')
data2

