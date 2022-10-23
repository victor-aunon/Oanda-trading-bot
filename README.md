 [![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://github.com/victor-aunon/Oanda-trading-bot/blob/develop/LICENSE) [![Tests](https://github.com/victor-aunon/Oanda-trading-bot/actions/workflows/tests.yml/badge.svg)](https://github.com/victor-aunon/Oanda-trading-bot/actions/workflows/tests.yml)  <a href="https://www.buymeacoffee.com/victoraunon" target="_blank"><img  height="40px" src="https://cdn.buymeacoffee.com/buttons/v2/default-blue.png" alt="Buy Me A Coffee" style="height: 20px !important;width: 72px !important;" ></a>

## Table of contents
 - [Strategy description](#strategy-description)
 - [Installing the package](#installing-the-package)
 - [Setting up the bot](#setting-up-the-bot)
     - [Creating an OANDA account and an access token](#creating-an-oanda-account-and-an-access-token)
     - [Creating a Telegram bot](#creating-a-telegram-bot-optional)
 - [Running the bot (live trading)](#running-the-bot-live-trading)
     - [The configuration file (live trading)](#the-configuration-file-live-trading)
 - [Backtesting](#backtesting)
     - [The configuration file (backtesting)](#the-configuration-file-backtesting)
 - [Optimizing](#optimizing)
     - [The configuration file (optimizing)](#the-configuration-file-optimizing)
 - [Testing](#testing)

---

# Oanda trading bot

This is a trading bot intended to trade forex and crytocurrencies CFD contracts
within the OANDA trading platform. It is based on the [Backtrader](https://www.backtrader.com/) python trading library, but it makes use of the OANDA API to deal with orders and trades.

## Strategy description

The trading strategy is based on the **MACD** ([see MACD in Stockcharts](https://school.stockcharts.com/doku.php?id=technical_indicators:moving_average_convergence_divergence_macd)) and a slow **EMA** ([see EMA in Stockcharts](https://school.stockcharts.com/doku.php?id=technical_indicators:moving_averages)) to catch the main trend of the market. The strategy is defined in the `MACDEMAATRStrategy` class in the `src/oandatradingbot/oandabot.py` file. A thorough explanation of the strategy can be found in the [tradingrush.net](https://tradingrush.net/i-risked-macd-trading-strategy-100-times-heres-what-happened/) web and YouTube channel.

In order to set the _stop loss_ for every order, the **Average True Range** ([see ATR in Stockcharts](https://school.stockcharts.com/doku.php?id=technical_indicators:average_true_range_atr)). The _take profit_ limit is calculate based on the stop loss multiplied by the _profit-risk ratio_. This parameters can be tweaked in the configuration file.

Tests have been carried out with a timeframe of **5 minutes**, but the user is able to change the timeframe in the configuration file.

## Installing the package

You can install the package using any of the methods shown below:

- Install it from GitHub: just run `pip install git+https://github.com/victor-aunon/Oanda-trading-bot`

- Download the code from [https://github.com/victor-aunon/Oanda-trading-bot](https://github.com/victor-aunon/Oanda-trading-bot) and install the dependencies by running `pip install -r requirements.txt` within the project folder.

## Setting up the bot

### **Creating an OANDA account and an access token**

The bot requires a valid OANDA account as well as a valid token to get access to the REST API. You can create an account at [https://www.oanda.com/apply/](https://www.oanda.com/apply/) and create a token at [http://developer.oanda.com/rest-live-v20/introduction/](http://developer.oanda.com/rest-live-v20/introduction/).The access token is required to create the OANDA store of the [btoandav20](https://github.com/happydasch/btoandav20) python library.

After log into your account you will see a panel like this:
![panel](/readme_files/log-in.jpg)

If you click on **Manage API Access** you will be redirected to a page where you can generate a new token:
![token](/readme_files/token.jpg)

The bot also requires your account ID number, it can be found by clicking on the **View** button under **Manage Funds** in the previous account panel. Make sure to copy the number next to **v20 Account Number**:
![account-id](/readme_files/account-id.jpg)

### **Creating a Telegram bot (optional)**

Since version 1.1.0, the bot is able to notify trades and send daily and weekly reports through Telegram. To use this function, a Telegram bot has to be created. The creation process is explain in the next steps: 

 1. Go to Telegram and open a chat with **BotFather**
 2. You can type `/start` to see a complete list of all the commands you can run or directly type `/newbot` to create a new bot.
 3. BotFather will ask you to name your bot and assign a username for that bot.
 4. Once the username is valid, BotFather will prompt you a message including the **access token** for your bot.
 5. You will also need your chat id so open a new chat with your newly created bot and type something to active the bot.
 6. Go to the following url: `https://api.telegram.org/bot<your bot access token>/getUpdates`. At this point you should see a JSON response in your web browser. Look for the `chat` field and write down the number value of the `id` field (not to be confused with `update_id` or `message_id`).

## Running the bot (live trading)

The following section covers how to run the bot for live trading, either on a paper or brokerage account. If you want to backtest a strategy, jump to [Backtesting](#backtesting) section.

### **The configuration file (live trading)**

 In order to run the bot, a valid configuration JSON file must be created. A sample of the configuration file can be found in `src/oandatradingbot/config.json` which contains the following keys:

 - **`database_uri`**: A string representing the address of the trades database. If omitted, the bot will create a sqlite database in `/src/oandatradingbot/trades.db`.
 - **`oanda_token`**: A string representing the OANDA access token explained in [OANDA token section](#creating-an-oanda-account-and-an-access-token).
 - **`oanda_account_id`**: A string representing the OANDA account ID number explained in [OANDA token section](#creating-an-oanda-account-and-an-access-token).
 - **`practice`**: `true` if you want to use the OANDA test environment, otherwise `false`.
 - **`timeframe`**: A string representing the timeframe to trade the market e.g. `"Minutes"`. Check valid values in the [Backtrader documentation](https://www.backtrader.com/docu/live/oanda/oanda/#oandadata).
 - **`timeframe_num`**: The timeframe to trade the market. For example, if you selected `"Minutes"`, then this value can be 1, 5, 10 ... Check valid values in the [Backtrader documentation](https://www.backtrader.com/docu/live/oanda/oanda/#oandadata).
 - **`instruments`**: An array with the pair of currencies to trade, e.g. `["EUR_USD", "ETH_USD"]`.
 - **`risk`**: A float value indicating the cash percentage to be risked per trade (`1.0` = 1%).
 - **`account_currency`**: The currency of your OANDA account, e.g. `"EUR"` for euros.
 - **`telegram_token`**: A string representing your Telegram bot access token described in [Telegram bot section](#creating-a-telegram-bot-optional) (optional).
 - **`telegram_chat_id`**: A string representing your chat id described in [Telegram bot section](#creating-a-telegram-bot-optional) (optional).
 - **`telegram_report_frequency`**: The frequency of the trading reports sent by the Telegram bot. Valid values are:
     - `"Trade"`: each trade will be notified. Daily and weekly reports will be sent as well.
     - `"Daily"`: Daily and weekly reports will be sent by the bot. Trade results will be skipped. **Default value**.
     - `"Weekly"`: Only weekly reports will be sent by the bot. Trade results will be skipped. Weekly report is sent on Fridays.
 - **`telegram_report_hour`**: And integer representing the local hour at which the daily and weekly reports are notified. **Default value is 22**.
 - **`language`**: A string representing the language used to print the trading bot messages to the console. Valid values are `"ES-ES"` and `"EN-US"`.
 - **`tts`**: `true` if you want to enable the text to speech (voice messages), otherwise `false`. The TTS API is based on [pyttsx3](https://pyttsx3.readthedocs.io/en/latest/) and uses sapi5 (Windows), nsss (MacOS X) and espeak (other platform) tts engines. These engines have to be installed on your system in order to use pyttsx3. Please check [pyttsx3 documentation](https://pyttsx3.readthedocs.io/en/latest/). Also any language set in `language_tts` has to be installed on your machine.
 - **`language_tts`**: A string representing the language used by the Text To Speech (TTS) system.
 - **`strategy_params`**: A JSON object representing the main parameters of the trading strategy:
     - **`macd_fast_ema`**: the period of the MACD fast EMA as an integer. Default value is 12.
     - **`macd_slow_ema`**: the period of the MACD slow EMA as an integer. Default value is 26.
     - **`macd_signal_ema`**: the period of the MACD signal EMA as an integer. Check MACD indicator in [Stockcharts](https://school.stockcharts.com/doku.php?id=technical_indicators:moving_average_convergence_divergence_macd). Default value is 9.
     - **`ema_period`**: the period of the long period ema. Check EMA indicator in [Stockcharts](https://school.stockcharts.com/doku.php?id=technical_indicators:moving_averages). Default value is 200.
     - **`atr_period`**: the period of the average true range. Check ATR indicator in [Stockcharts](https://school.stockcharts.com/doku.php?id=technical_indicators:average_true_range_atr). Default value is 14.
     - **`atr_distance`**: a multiplier of the average true range to set the stop loss price. Default value is 1.2.
     - **`profit_risk_ratio`**: a multipier of the stop loss to set the take profit price. Default value is 1.5.

You can run the bot directly from the command line with `python -m oandatradingbot` using the following arguments:

- **`--config-file`**: followed by the JSON configuration file. If omitted, the bot will use the file in `/src/oandatradingbot/config.json`.
- **`--debug`**: by adding this argument, the bot will show more information to the console.

## Backtesting

**_Note: You DO NOT need an OANDA account to backtest your strategy_**

### **The configuration file (backtesting)**

A sample of the configuration file can be found in `src/oandatradingbot/config_backtest.json` which contains the following keys:

 - **`results_path`**: An array representing the path where backtesting results will be saved.
 - **`instruments`**: An array with the pair of currencies to trade, e.g. `["EUR_USD", "ETH_USD"]`.
 - **`cash`**: A float value indicating the starting cash.
 - **`risk`**: A float value indicating the cash percentage to be risked per trade (`1.0` = 1%).
 - **`account_currency`**: The currency of your OANDA account, e.g. `"EUR"` for euros.
 - **`timeframe`**: A string representing the timeframe to trade the market e.g. `"Minutes"`. Check valid values in the [Backtrader documentation](https://www.backtrader.com/docu/live/oanda/oanda/#oandadata).
 - **`timeframe_num`**: The timeframe to trade the market. For example, if you selected `"Minutes"`, then this value can be 1, 5, 10 ... Check valid values in the [Backtrader documentation](https://www.backtrader.com/docu/live/oanda/oanda/#oandadata).
 - **`interval`**: A string representing the timeframe interval in a valid **yfinance** format. It must represent the same timeframe as `timeframe` and `timeframe_num`. So if these fields were `"Minutes"` and `5`, **`interval`** would be `"5m"`. Valid intervals are `1m,2m,5m,15m,30m,60m,90m,1h,1d,5d,1wk,1mo,3mo`.
 - **`language`**: A string representing the language used to print the trading bot messages to the console. Valid values are `"ES-ES"` and `"EN-US"`.
 - **`strategy_params`**: A JSON object representing the main parameters of the trading strategy:
     - **`macd_fast_ema`**: the period of the MACD fast EMA as an integer. Default value is 12.
     - **`macd_slow_ema`**: the period of the MACD slow EMA as an integer. Default value is 26.
     - **`macd_signal_ema`**: the period of the MACD signal EMA as an integer. Check MACD indicator in [Stockcharts](https://school.stockcharts.com/doku.php?id=technical_indicators:moving_average_convergence_divergence_macd). Default value is 9.
     - **`ema_period`**: the period of the long period ema. Check EMA indicator in [Stockcharts](https://school.stockcharts.com/doku.php?id=technical_indicators:moving_averages). Default value is 200.
     - **`atr_period`**: the period of the average true range. Check ATR indicator in [Stockcharts](https://school.stockcharts.com/doku.php?id=technical_indicators:average_true_range_atr). Default value is 14.
     - **`atr_distance`**: a multiplier of the average true range to set the stop loss price. Default value is 1.2.
     - **`profit_risk_ratio`**: a multipier of the stop loss to set the take profit price. Default value is 1.5.

You can run the backtest directly from the command line with `python -m oandatradingbot.backtester` using the following arguments:

- **`--config-file`**: followed by the JSON configuration file. If omitted, the bot will use the file in `/src/oandatradingbot/config_backtest.json`.
- **`--debug`**: by adding this argument, the bot will show more information to the console.

In the **`results_path`** you will find two files:
 - A **.xlsx** file containing two sheets:
    - *Trades*: This sheet contains a list of all the trades executed during the backtest.
    - *Summary*: This sheet contains a summary of the backtest strategy with the values also printed to the console at the end of the backtest.
 - A **.png** file with different subplots of the strategy: Cash, value, trades, the instrument candlechart and the indicators charts.

## Optimizing

**_Note: You DO NOT need an OANDA account to optimize your strategy_**

### **The configuration file (optimizing)**

A sample of the configuration file can be found in `src/oandatradingbot/config_optimize.json` which contains the following keys:

 - **`results_path`**: An array representing the path where backtesting results will be saved.
 - **`instruments`**: An array with the pair of currencies to trade, e.g. `["EUR_USD", "ETH_USD"]`.
 - **`cash`**: A float value indicating the starting cash.
 - **`risk`**: A float value indicating the cash percentage to be risked per trade (`1.0` = 1%).
 - **`account_currency`**: The currency of your OANDA account, e.g. `"EUR"` for euros.
 - **`timeframe`**: A string representing the timeframe to trade the market e.g. `"Minutes"`. Check valid values in the [Backtrader documentation](https://www.backtrader.com/docu/live/oanda/oanda/#oandadata).
 - **`timeframe_num`**: The timeframe to trade the market. For example, if you selected `"Minutes"`, then this value can be 1, 5, 10 ... Check valid values in the [Backtrader documentation](https://www.backtrader.com/docu/live/oanda/oanda/#oandadata).
 - **`interval`**: A string representing the timeframe interval in a valid **yfinance** format. It must represent the same timeframe as `timeframe` and `timeframe_num`. So if these fields were `"Minutes"` and `5`, **`interval`** would be `"5m"`. Valid intervals are `1m,2m,5m,15m,30m,60m,90m,1h,1d,5d,1wk,1mo,3mo`.
 - **`strategy_params`**: A JSON object representing the main parameters of the trading strategy:
     - **`macd_fast_ema`**: the period of the MACD fast EMA. It can be either a single value, a list of values or an object composed of three fields (`start`, `end` and `step`) defining an evenly spaced list of numbers over the interval `[start, end[`.
     - **`macd_slow_ema`**: the period of the MACD slow EMA. It can be either a single value, a list of values or an object composed of three fields (`start`, `end` and `step`) defining an evenly spaced list of numbers over the interval `[start, end[`.
     - **`macd_signal_ema`**: the period of the MACD signal EMA. It can be either a single value, a list of values or an object composed of three fields (`start`, `end` and `step`) defining an evenly spaced list of numbers over the interval `[start, end[`.
     - **`ema_period`**: the period of the long period ema. It can be either a single value, a list of values or an object composed of three fields (`start`, `end` and `step`) defining an evenly spaced list of numbers over the interval `[start, end[`.
     - **`atr_period`**: the period of the average true range. It can be either a single value, a list of values or an object composed of three fields (`start`, `end` and `step`) defining an evenly spaced list of numbers over the interval `[start, end[`.
     - **`atr_distance`**: a multiplier of the average true range to set the stop loss price. It can be either a single value, a list of values or an object composed of three fields (`start`, `end` and `step`) defining an evenly spaced list of numbers over the interval `[start, end[`.
     - **`profit_risk_ratio`**: a multipier of the stop loss to set the take profit price. It can be either a single value, a list of values or an object composed of three fields (`start`, `end` and `step`) defining an evenly spaced list of numbers over the interval `[start, end[`.

You can run the optimizer directly from the command line with `python -m oandatradingbot.optimizer` using the following argument:

- **`--config-file`**: followed by the JSON configuration file. If omitted, the bot will use the file in `/src/oandatradingbot/config_optimize.json`.

By default, the optimizer will backtest all the different parameter combinations using multiprocessing. So if the computer CPU has eight cores, eight combinations are backtested in parallel.

In the **`results_path`** you will find a folder named `Optimization_YYYY-MM-DD_HH-mm` containing:
 - A **.xlsx** file with a summary of the main results for each parameters combination: trades, won, lost, win rate, trades per instrument, etc.
 - Different **.png** charts showing results for the best **30 (max) combinations** sorted by the SQN ([System Quality Number](https://tradingtact.com/system-quality-number/)) indicator:
    - A chart showing the cumulative returns per instrument, as a percentage with respect to the initial cash.
    - A chart showing the win rate (trades won / total trades) per instrument in percentage.
    - A chart showing the number of total trades per instrument.
 - Two **.png** charts for each strategy parameter:
    - One showing a distribution of the win rate for each value of the parameter during the optimization.
    - Another on showing a distribution of the number of trades for each value of the parameter during the optimization.

## Testing

Tests files are run automatically on GitHub. However, if you want to run those files, the following environment variables have to be created in your system:

- `oanda_token`
- `oanda_account_id`
- `telegram_token`
- `telegram_chat_id`
