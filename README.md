
![yuzu logo](.asets/../assets/yuzu-logo.png)

Yuzu is an open source automated trading bot written in Python. It features exchange specific backtesting, custom strategy making, strategy optimization, adaptive graph plotting, paper trading, and soon will feature live trading.

# How Does It Work

overview, basic steps, in depth steps?

# Usage

## How to [Create a Custom Strategy](./assets/custom-strategy.md)

## How to [Optimize Strategy Parameters](./assets/optimize-strategy.md)

# Features

- [x] <img src=".asets/../assets/strategy-icon.png" width="15" height="15"> **support custom strategy making** _(quickly add your own strategy functions)_

- [x] <img src=".asets/../assets/graph-icon.png" width="15" height="15"> **adaptive graph plot** _(templated graphing function)_
  ![demo plot](.asets/../assets/demo-plot.png)
- [x] <img src=".asets/../assets/genalgo-icon.png" width="15" height="15"> **optimize strategies** _(optimize strategy parameters using machine learning)_
- [ ] <img src=".asets/../assets/python-icon.png" width="15" height="15"> **package project** _(install using PyPI to code with YUZU)_
- [ ] <img src=".asets/../assets/terminal-icon.png" width="15" height="15"> **cli** _(command-line interface to use YUZU)_
- [ ] <img src=".asets/../assets/gui-icon.png" width="15" height="15"> **gui** _(React-based user interface to use YUZU)_

## Exchange Support

- [x] <img src=".asets/../assets/paper-wallet-icon.png" width="15" height="15"> **PaperWallet** _(used by any exchange to paper trade)_
- [ ] <img src=".asets/../assets/binance-logo.png" width="15" height="15"> **BinanceUS**
  - [x] **historical data** _(pull data to backtest)_
  - [ ] **live trading** _(create websocket to start live trading)_
  - [ ] **user info** _(pull user account information)_
- [ ] <img src=".asets/../assets/coinbase-pro-logo.png" width="20" height="14"> **CoinbasePro**
  - [ ] **historical data** _(pull data to backtest)_
  - [ ] **live trading** _(create websocket to start live trading)_
  - [ ] **user info** _(pull user account information)_
- [ ] <img src=".asets/../assets/kraken-logo.png" width="20" height="14"> **Kraken**
  - [ ] **historical data** _(pull data to backtest)_
  - [ ] **live trading** _(create websocket to start live trading)_
  - [ ] **user info** _(pull user account information)_

# Future Development

## **PHASE 0:**

Yuzu is a project still in development, it can be cloned and
