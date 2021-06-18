
def quantity_calculator(risk_per_trade, sl, enter_price, money_available):
    money_traded = money_available / 2
    quantity = money_traded / enter_price
    quantity = quantity.__round__(3)

    if sl < enter_price:
        percentage_risked_trade = (1 - sl / enter_price) * 100  # Ex : 0.5% for long
    else:
        percentage_risked_trade = (1 - enter_price / sl) * 100  # short

    percentage_risked_trade = percentage_risked_trade / 2
    real_money_traded = quantity * enter_price
    leverage = ((1 - risk_per_trade) * 100) / (percentage_risked_trade / 100 * real_money_traded)
    leverage = leverage.__round__()

    print(leverage * percentage_risked_trade * 2)

    if leverage * percentage_risked_trade * 2 >= 100:
        print("High risk of liquidation !")
    if leverage >= 125:
        print("Leverage too high. The platform cannot handle it.")
    elif leverage >= 90:
        print("Very high leverage ! Think about putting more money in the trade !")
    elif leverage < 1:
        leverage = 1

    print("The quantity is : " + str(quantity) + " BTC")
    print("The leverage is : " + str(leverage))
    print("The money traded is : " + str(real_money_traded))

    return quantity, leverage to m