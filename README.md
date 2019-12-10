Backtrade 0.1

This simple app was created firstly just to download free stock data and to calculate buy/sell signals.
After that there was need for backtesting so new feutures were added.
For now it is just dumb app for:
- Actualize data from Alphavantage and save it to csv files
- Read data from CSV
- Calculate buy/sell signals
- Backtest test strategy

Installation:
Due to working with csv files, it was determined that the best place to save tham will be in Home folder in Documents.
Thanks to this the pip has to be called with --no-binary argument so for saving data is used absolute path and not relative.
Also the app is not registered at pip, so for instalation use:
pip install --no-binary :all: git+https://github.com/jnihnat/Momentum-QQQ-GLD

To Do
next feutures to be implemented:
- console input arguments with argparse
- more Stocks
- and more :)
