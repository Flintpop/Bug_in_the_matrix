# PythonTrader
## Summary
Automated trading bot.

This bot follows a relatively complex strategy of trading. He detects the chosen pattern, check if he can buy, uses leverage to match the desired maximum amount of loss per trade and then buys and sells back. 
Once all of this is done, he sends an email communicating the results.

The bot can stop if random error occurs but he will send the traceback by email. If the error occurs whilst a trade is occuring, he sells it to prevent further potential losses.

## Strategies
There are two main strategies. 

The first one was developped in june, july, august (alpha), september and a bit in october (beta).
The second one was developped in february and a tiny bit in march, with very short developpement time thanks to my experience gained, less complexity required by the strategy itself, and much better planning.
#### MACD Divergence
This strategy is based on a simple but rare and difficult regognizable pattern of divergence between MACD lines and price action, along with the global trend to decide if it will be a long or a short. However, long results are too weak, so the bot only shorts.
The selling signal is simply a sell order that is calculated pre-emptively.
#### Ema Fractals
This strategy uses the background trend to decide whether to long or short. When the price action bounce back from the ema, but with specific conditions, and the Bill William fractal is green, the bot buys.
The selling signal is simply a sell order that is calculated pre-emptively.

## Current state of the project
Discontinued, and need an overhaul / major refactoring. There is a lot of old code that would be written differently today, but since I had less experience, I wrote it in this way.

## What could have been done better
More commented code, for myself. More reading of API documentation, and I should have been trying to know, understand problems beforehand on paper.
I should have searched for more (and more often) similar projects online, and learn from them. 
Better planning would have been a time saver too.

## Final notes
On this project there is voluntarily no backtesting code. This was developped on another project.

This bot used binance trading API to buy and sells with leverage thanks to binance futures. This service is no longer available in France, so that's one of the reasons why I stopped this project.
They offered the most advantageous trading fees, which partly enabled my strategies to be profitable.
