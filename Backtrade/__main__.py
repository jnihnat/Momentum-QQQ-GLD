import pandas as pd
import datetime as dt
import Backtrade.Financnik_SMO_PRO as FSP
from Backtrade import Strategy_Calculations as SC
import os

home = os.path.expanduser("~")
BT_home = str(home + '/Documents/Backtrade/')
stock_companies = {
    "1": "NDX",
    "2": "SPX"
}
strategies = {
    "1": "SmoProUpgraded",
    "2": "SmoProFinancnik"
}




def nacitaj_data(symbol='NDX', st_date=dt.date(2017, 1, 1)):
    # tickers = tickers.columns.values.tolist()
    tickers = ['QQQ', 'SPY']
    data = pd.DataFrame()
    for t in tickers:
        # time.sleep(12)
        data_pom = pd.read_csv('Data/StockData/'+t+'.csv')
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


if __name__ == '__main__':
    SC.kontext_filt()
    chose = input("What you wont to do?\n"
                  "Run backtest on strategy - 1\n"
                  "Run filter creation for strategy - 2\n"
                  "")
    if chose == "1":
        FSP.run()
    elif chose == "2":
        chose_stocks = input("For what index companies you want to create filter?\n"
                             "Nasdaq 100 - 1\n"
                             "SPY 500 - 2\n"
                             "")
        strategy = input("For what strategy you want to create filter?\n"
                         "SMO PRO Upgraded - 1\n"
                         "SMO PRO Financnik - 2\n"
                         "")
        date = input("For what date you want to create filter?\n"
                     "Please use format YYYY-MM-DD\n"
                     )
        date = dt.datetime.fromisoformat(str(date+" 09:31"))
        date = SC.BussDay(actual_date=date)
        strdate = date.strftime("%Y-%m-%d")
        csv_name = str(BT_home + "Calculated_Tables/" + strategies[strategy] + "_" + strdate + ".csv")
        if os.path.exists(csv_name):
            print("Calculated filter from past: ", csv_name)
        else:
            datas = SC.DATA(stock_companies[chose_stocks])
            datas.ReloadDataFromAV()
            datas.ReadDataCSV()
            datas.data = datas.data[
                       ((datas.data.index.get_loc(key=str(strdate))) - 500): (datas.data.index.get_loc(key=str(strdate))) + 1
                       ]
            my_class = SC.StrategieCalculations(datas.data)
            func = getattr(my_class, strategies[strategy])
            func(date, port_value=55000)
            print("Calculated filter: ", csv_name)

    else:
        exit(200)

