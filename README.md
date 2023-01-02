# PythonTrader
## Summary
Automated trading bot.

This bot follows a relatively complex strategy of trading. He detects the chosen pattern, check if he can buy, uses leverage to match the desired maximum amount of loss per trade and then buys and sells back. 
Once all of this is done, he sends an email communicating the results.

The bot can stops if random error occurs but will send the traceback by email. If the error occurs whilst a trade is occuring, he sells it to prevent further potential losses.

## Strategies
There are two main strategies. 

The first one was developped in june, july, august (alpha), september and a bit in october (beta).
The second one was developped in february and a tiny bit in march I believe, with very short developpement time thanks to my experience gained, less complexity and planning.
#### MACD Divergence
This strategy is based on a simple but rare and difficult regognizable pattern of divergence between MACD lines and price action, along with the global trend to decide if there is long or short. However, long results are too poor to be used, so the bot only shorts.
The selling signal is simply a sell order that is calculated pre-emptively.
#### Ema Fractals
This strategy uses the background trend to decide whether to long or short. When the price action bounce back from the ema, but with specific conditions, and the Bill William fractal is green, the bot buys.
The selling signal is simply a sell order that is calculated pre-emptively.

## What could have been done better
More comments of the code, for myself. Reading API documentation, and getting to know problems beforehand on paper.
Seeking more and more often similar projects online, and learning from them.

## Final notes
On this project there is voluntarily no backtesting. This was developped on another project.

This bot used binance trading API to buy and sells with leverage thanks to binance futures. This service is no longer available in France, so that's a reason why I stopped this project.
They offered the most advantageous trading fees.
