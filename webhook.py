import json, config
from flask import Flask, request
from binance.client import Client
from binance.enums import *

app = Flask(__name__)

## client = Client(config.API_KEY, config.API_SECRET, tld='us')

def order(side, quantity, symbol, order_type=ORDER_TYPE_MARKET):
    try:
        print("sending order")
        order = client.create_order(symbol=symbol, side=side, type=order_type, quantity=quantity)
        print(order)
    except Exception as e:
        print("an exception occured - {}".format(e))
        return False

    return True

@app.route("/")
def hello_world():
    return "Hello, World!"

@app.route("/test_debug")
def whatever():
    return "this is the test route"

@app.route("/webhook", methods=['POST'])
def webhook():
    #print(request.data)
    data = json.loads(request.data)

    if data['passphrase'] != config.WEBHOOK_PASSPHRASE:
        return {
            "code": "error",
            "message": "invalid passphrase"
        }
    
    side = data['strategy']['order_action'].upper()
    quantity = data['strategy']['order_contracts']
    order_response = order(side, quantity, "BTCUSD")

    if order_response:
        return {
            "code": "success",
            "message": "order executed"
        }
    else:
        print("order failed")

        return {
            "code": "error",
            "message": "order failed"
        }

    # print(data['ticker'])
    # print(data['bar'])

    # return {
    #     "code": "success",
    #     "message": data
    # }