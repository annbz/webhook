# connect and place order for basic

from flask import Flask, request, jsonify
import json, requests
import config_demo
from ctrader_open_api import Client, Protobuf, TcpProtocol, EndPoints
import ctrader_open_api.messages.OpenApiMessages_pb2 as OA
import ctrader_open_api.messages.OpenApiModelMessages_pb2 as OAModel
import ctrader_open_api.messages.OpenApiCommonMessages_pb2 as OACommon
import ctrader_open_api.messages.OpenApiCommonModelMessages_pb2 as OAModelCommon
from twisted.internet import reactor
import threading

app = Flask(__name__)

# cTrader API credentials
# ACCESS_TOKEN = "YOUR_CTRADER_ACCESS_TOKEN"
# ACCOUNT_ID = "YOUR_CTRADER_ACCOUNT_ID"
# BASE_URL = "https://live.ctraderapi.com"

# credentials = json.load(open('credentials_demo.json'))
client = Client(EndPoints.PROTOBUF_DEMO_HOST, EndPoints.PROTOBUF_PORT, TcpProtocol)
PROTO_OA_ERROR_RES_PAYLOAD_TYPE = OA.ProtoOAErrorRes().payloadType

symbol = "BTCSUD"
side = "SELL"
quantity = 100

def main():
    req = OA.ProtoOANewOrderReq()
    req.ctidTraderAccountId = credentials['accountId']

    # req.orderType = OAModel.ProtoOAOrderType.LIMIT
    req.orderType = OAModel.ProtoOAOrderType.MARKET

    if side == "BUY":
        req.tradeSide = OAModel.ProtoOATradeSide.BUY
    elif side == "SELL":
        req.tradeSide = OAModel.ProtoOATradeSide.SELL

    if symbol == "XAUUSD":    
        req.symbolId = 41 # XAUUSD
    else:
        print('Please reset symbol again!')
        return   
    
    #req.limitPrice = 3099.34
    req.volume = quantity # equals 0.01 lot
    #req.stopLoss = 3000.34
    #req.takeProfit = 3200.34
    deferred = client.send(req)
    deferred.addCallbacks(onNewOrderRes, onError)

def onNewOrderRes(message):
    if message.payloadType != OA.ProtoOAExecutionEvent().payloadType:
        print('order not placed')
        return
    response = Protobuf.extract(message)
    print('order successfully placed');
    print('order id:', response.order.orderId)

def onAccAuth(message):
    if message.payloadType == PROTO_OA_ERROR_RES_PAYLOAD_TYPE:
        print('account authentication failed', '\n')
        print(Protobuf.extract(message), '\n')
        return
    print('account authenticated')
    main()

def onAppAuth(message):
    if message.payloadType == PROTO_OA_ERROR_RES_PAYLOAD_TYPE:
        print('app authentication failed', '\n')
        print(Protobuf.extract(message), '\n')
        return
    print('app authenticated')
    req = OA.ProtoOAAccountAuthReq()
    req.ctidTraderAccountId = config_demo.ACCOUNT_ID
    req.accessToken = config_demo.ACCESS_TOKEN
    deferred = client.send(req)
    deferred.addCallbacks(onAccAuth, onError)

def onError(failure):
    print('err: ', repr(failure.value))

def connected(client):
    print('connected')
    req = OA.ProtoOAApplicationAuthReq()
    req.clientId = config_demo.Client_ID
    req.clientSecret = config_demo.Secret
    deferred = client.send(req, responseTimeoutInSeconds=20) # err if no response under 20 secs
    deferred.addCallbacks(onAppAuth, onError)

def disconnected(client, reason):
    print('disconnected: ', reason)

def onMsg(client, message):
    ignores = [i.payloadType for i in [OACommon.ProtoHeartbeatEvent(), OA.ProtoOAAccountAuthRes(), OA.ProtoOAApplicationAuthRes()]]
    if message.payloadType in ignores:
        return
    print('message received')

def send_order_to_ctrader(symbol, action, volume):
    try:
        print("sending order")
        #order = client.create_order(symbol=symbol, side=side, type=order_type, quantity=quantity)
        #print(order)

        client.setConnectedCallback(connected)
        client.setDisconnectedCallback(disconnected)
        client.setMessageReceivedCallback(onMsg)
        client.startService()
        reactor.run()

    except Exception as e:
        print("an exception occured - {}".format(e))
        return False

    return True

@app.route("/")
def hello_world():
    return "Hello, World!"

@app.route("/webhook_cbot", methods=['POST'])
def webhook():
    #print(request.data)
    data = json.loads(request.data)

    if data['passphrase'] != config_demo.WEBHOOK_PASSPHRASE:
        return {
            "code": "error",
            "message": "invalid passphrase"
        }
    global symbol
    global side
    global quantity

    symbol = data["ticker"]
    side = data['strategy']['order_action'].upper()
    quantity = data['strategy']['order_contracts']*100
    order_response = send_order_to_ctrader(side, quantity, symbol)

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
