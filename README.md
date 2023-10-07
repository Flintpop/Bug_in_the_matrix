# PythonTrader
## Summary
Automated trading bot.

This bot operates using one of two main trading strategies, each with its own complexity. It detects the selected pattern, checks if it can buy, employs leverage to match the desired maximum loss per trade, and then buys and sells back. Once all of these actions are completed, it sends an email communicating the results.

The bot can halt operations if a random error occurs but will send the traceback via email. If the error happens while a trade is ongoing, it will sell the position to prevent further potential losses.

## Strategies
There are two main strategies.

The first one was developed in June, July, August (alpha), September, and a bit in October (beta).
The second one was developed in February and a smidgen in March, with very short development time thanks to my accumulated experience, reduced complexity required by the strategy itself, and better planning.
#### MACD Divergence
This strategy is based on a simple yet rare and hard-to-recognize pattern of divergence between MACD lines and price action, along with the overall trend to decide whether it will be a long or a short. However, long positions yield weak results, so the bot only goes short. 
The sell signal is simply a pre-emptively calculated sell order.
#### EMA Fractals
This strategy utilizes the background trend to decide whether to go long or short. When the price action bounces back from the EMA under specific conditions, and the Bill Williams fractal is green, the bot buys. 
The sell signal is simply a pre-emptively calculated sell order.

## Current State of the Project
Discontinued and in need of an overhaul or major refactoring. There is a lot of legacy code that would be written differently today, but since I had less experience back then, it was written in that manner.

## What Could Have Been Done Better
More commented code, for my own benefit. More in-depth reading of API documentation, and I should have aimed to know and understand potential problems on paper beforehand. 
I should have also looked for more (and more frequent) similar projects online to learn from them. 
Better planning would have also saved time.

## Final Notes
There is intentionally no backtesting code in this project. This was developed in another project.

This bot used the Binance trading API to buy and sell with leverage via Binance Futures. This service is no longer available in France, which is one of the reasons why I stopped this project. 
They offered the most advantageous trading fees, which partially enabled my strategies to be profitable.
