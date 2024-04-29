import pandas as pd

def get_account_info(client):
    info = client.get_account()
    print(info)
    
def get_withdraw_history(client):
    withdraws = client.get_withdraw_history()
    print(withdraws)
    
def get_futures_balance(client):
    balance = client.futures_account_balance()
    balance_df = pd.DataFrame(balance)
    
    usdt_balance = float(balance_df[balance_df['asset']=='USDT']['balance'].iloc[0])
    btc_balance = float(balance_df[balance_df['asset']=='BTC']['balance'].iloc[0])
    print(f'usdt_balance: {usdt_balance} / btc_balance: {btc_balance}')
    
def get_all_orders(client, status=None):
    orders = client.futures_get_all_orders(symbol='BTCUSDT')
    orders_df = pd.DataFrame(orders)
    if status is None:
        print(orders_df[['time','updateTime','avgPrice','origQty','side','positionSide','status','stopPrice']])
    else:
        print(orders_df[orders_df['status']==status][['time','updateTime','avgPrice','origQty','side','positionSide','status','stopPrice']])   

def futures_change_leverage(client, leverage):
    leverage_change = client.futures_change_leverage(symbol='BTCUSDT',
                                                     leverage=leverage)
    print(leverage_change)
    
def get_max_order_info(client, leverage, max_ratio=0.99, fee_rate=0.0005):
    balance = client.futures_account_balance()
    balance_df = pd.DataFrame(balance)
    usdt_balance = float(balance_df[balance_df['asset']=='USDT']['balance'].iloc[0])
    
    mark_price = float(client.futures_mark_price(symbol='BTCUSDT')['markPrice'])
    max_quantity = round(usdt_balance/(mark_price*(1+fee_rate)), 4) * leverage * max_ratio
    return mark_price, max_quantity