import setuptools
from glob import glob
from os.path import expanduser

with open("README.md", "r") as fh:
    long_description = fh.read()

home = expanduser('~')
BT_home = str(home + '/Documents/Backtrade/')

setuptools.setup(
    name="Backtrade",
    version="0.0.1",
    author="Jan Ihnat",
    author_email="jnihnat@gmail.com",
    description="Backtrading function",
    long_description=long_description,
    long_description_content_type="text/markdown",
    data_files=[(BT_home+'IndexData', ['Backtrade/Data/IndexData/NASDAQ100.csv']), (BT_home+'StockData', glob('Backtrade/Data/StockData/**'))],
    #include_package_data=True,
    url="https://github.com/jnihnat/Momentum-QQQ-GLD",
    entry_points={"console_scripts": ["Backtrade = Backtrade.Financnik_SMO_PRO:run"]},
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ]
)