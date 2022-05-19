 [![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://github.com/victor-aunon/Oanda-trading-bot/blob/develop/LICENSE) [![Tests](https://github.com/victor-aunon/Oanda-trading-bot/actions/workflows/tests.yml/badge.svg)](https://github.com/victor-aunon/Oanda-trading-bot/actions/workflows/tests.yml)  <a href="https://www.buymeacoffee.com/victoraunon" target="_blank"><img  height="40px" src="https://cdn.buymeacoffee.com/buttons/v2/default-blue.png" alt="Buy Me A Coffee" style="height: 20px !important;width: 72px !important;" ></a>

## Table of contents
 - [Strategy description](#strategy-description)
 - [Installing the package](#installing-the-package)
 - [Setting up the bot](#setting-up-the-bot)
     - [Creating an OANDA account and an access token](#creating-an-oanda-account-and-an-access-token)
     - [Creating a Telegram bot](#creating-a-telegram-bot-optional)
     - [Creating the configuration file](#creating-the-configuration-file)
 - [Running the bot](#running-the-bot)
 - [Testing](#testing)

---

# Oanda trading bot

This is a trading bot intended to trade forex and crytocurrencies CFD contracts
within the OANDA trading platform. It is based on the [Backtrader](https://www.backtrader.com/) python trading library, but it makes use of the OANDA API to deal with orders and trades.

## Strategy description

The trading strategy is based on the **MACD** ([see MACD in Stockcharts](https://school.stockcharts.com/doku.php?id=technical_indicators:moving_average_convergence_divergence_macd)) and a slow **EMA** ([see EMA in Stockcharts](https://school.stockcharts.com/doku.php?id=technical_indicators:moving_averages)) to catch the main trend of the market. The strategy is defined in the `MACDEMAATRStrategy` class in the `src/tradingbot/oandabot.py` file. A thorough explanation of the strategy can be found in the [tradingrush.net](https://tradingrush.net/i-risked-macd-trading-strategy-100-times-heres-what-happened/) web and YouTube channel.

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

 ### **Creating the configuration file**

 A sample of the JSON configuration file can be found in `src/tradingbot/config.json` which contains the following keys:

 - **`database_uri`**: A string representing the address of the trades database. If omitted, the bot will create a sqlite database in `/src/oandatradingbot/trades.db`.
 - **`oanda_token`**: A string representing the OANDA access token explained in [OANDA token section](#creating-an-oanda-account-and-an-access-token).
 - **`oanda_account_id`**: A string representing the OANDA account ID number explained in [OANDA token section](#creating-an-oanda-account-and-an-access-token).
 - **`practice`**: `true` if you want to use the OANDA test environment, otherwise `false`.
 - **`timeframe`**: A string representing the timeframe to trade the market e.g. `"Minutes"`. Check valid values in the [Backtrader documentation](https://www.backtrader.com/docu/live/oanda/oanda/#oandadata).
 - **`timeframe_num`**: The timeframe to trade the market. For example, if you selected `"Minutes"`, then this value can be 1, 5, 10 ... Check valid values in the [Backtrader documentation](https://www.backtrader.com/docu/live/oanda/oanda/#oandadata).
 - **`pairs`**: An array of the pair currencies to trade, e.g. `["EUR_USD", "ETH_USD"]`.
 - **`account_currency`**: The currency of your OANDA account, e.g. `"EUR"` for euros.
 - **`telegram_token`**: A string representing your Telegram bot access token described in [Telegram bot section](#creating-a-telegram-bot-optional) (optional).
 - **`telegram_chat_id`**: A string representing your chat id described in [Telegram bot section](#creating-a-telegram-bot-optional) (optional).
 - **`telegram_report_frequency`**: The frequency of the trading reports sent by the Telegram bot. Valid values are:
     - `"Trade"`: each trade will be notified. Daily and weekly reports will be sent as well.
     - `"Daily"`: Daily and weekly reports will be sent by the bot. Trade results will be skipped. **Default value**.
     - `"Weekly"`: Only weekly reports will be sent by the bot. Trade results will be skipped. Weekly report is sent on Fridays.
 - **`telegram_report_hour`**: And integer representing the local hour at which the daily and weekly reports are notified. **Default value is 22**.
 - **`language`**: A string representing the language used to print the trading bot messages to the console. It is also the language used by the Text To Speech (TTS) system. Valid values are `"ES-ES"` and `"EN-US"`.
 - **`tts`**: `true` if you want to enable the text to speech (voice messages), otherwise `false`. The TTS API is based on [pyttsx3](https://pyttsx3.readthedocs.io/en/latest/) and uses sapi5 (Windows), nsss (MacOS X) and espeak (other platform) tts engines. These engines have to be installed in your system in order to use pyttsx3. Please check [pyttsx3 documentation](https://pyttsx3.readthedocs.io/en/latest/).
 - **`strategy_params`**: A JSON object representing the main parameters of the trading strategy:
     - **`macd_fast_ema`**: the period of the MACD fast EMA as an integer. Default value is 5.
     - **`macd_slow_ema`**: the period of the MACD slow EMA as an integer. Default value is 26.
     - **`macd_signal_ema`**: the period of the MACD signal EMA as an integer. Check MACD indicator in [Stockcharts](https://school.stockcharts.com/doku.php?id=technical_indicators:moving_average_convergence_divergence_macd). Default value is 8.
     - **`ema_period`**: the period of the long period ema. Check EMA indicator in [Stockcharts](https://school.stockcharts.com/doku.php?id=technical_indicators:moving_averages). Default value is 220.
     - **`atr_period`**: the period of the average true range. Check ATR indicator in [Stockcharts](https://school.stockcharts.com/doku.php?id=technical_indicators:average_true_range_atr). Default value is 14.
     - **`atr_distance`**: a multiplier of the average true range to set the stop loss price. Default value is 1.1.
     - **`profit_risk_ratio`**: a multipier of the stop loss to set the take profit price. Default value is 1.5.

## Running the bot

You can run the bot directly from the command line with `python -m oandatradingbot` using the following arguments:

- **`--config-file`**: followed by the JSON configuration file. If omitted, the bot will use the file in `/src/oandatradingbot/config.json`.
- **`--debug`**: by adding this argument, the bot will show more information to the console.

## Testing

Tests files are run automatically on GitHub. However, if you want to run those files, the following environment variables have to be created in your system:

- `oanda_token`
- `oanda_account_id`
- `telegram_token`
- `telegram_chat_id`
