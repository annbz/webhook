from ctrader_open_api import Client, Protobuf, TcpProtocol, EndPoints
import ctrader_open_api.messages.OpenApiMessages_pb2 as OA
import ctrader_open_api.messages.OpenApiModelMessages_pb2 as OAModel
import ctrader_open_api.messages.OpenApiCommonMessages_pb2 as OACommon
from twisted.internet import reactor
import config_demo

# === Replace with your credentials ===
CLIENT_ID = config_demo.Client_ID
CLIENT_SECRET = config_demo.Secret
ACCESS_TOKEN = config_demo.ACCESS_TOKEN
ACCOUNT_ID = config_demo.ACCOUNT_ID  # Your cTrader demo/live account ID

client = Client(EndPoints.PROTOBUF_DEMO_HOST, EndPoints.PROTOBUF_PORT, TcpProtocol)

def on_symbols_list_res(message):
    response = Protobuf.extract(message)
    print(f"\n=== Available Symbols (Searching BTCUSD) ===")
    for symbol in response.symbol:
        if "XAUUSD" in symbol.symbolName.upper():
            print(f"Symbol Name: {symbol.symbolName}, Symbol ID: {symbol.symbolId}")
    print("\nYou can now stop the script. :)")
    reactor.stop()

def request_symbols_list():
    req = OA.ProtoOASymbolsListReq()
    req.ctidTraderAccountId = ACCOUNT_ID
    deferred = client.send(req)
    deferred.addCallbacks(on_symbols_list_res, onError)

def on_account_auth_res(message):
    print("✅ Account authenticated.")
    request_symbols_list()

def on_app_auth_res(message):
    print("✅ App authenticated.")
    req = OA.ProtoOAAccountAuthReq()
    req.ctidTraderAccountId = ACCOUNT_ID
    req.accessToken = ACCESS_TOKEN
    deferred = client.send(req)
    deferred.addCallbacks(on_account_auth_res, onError)

def onError(failure):
    print("❌ Error:", failure)

def connected(client):
    print("🔌 Connected to cTrader.")
    req = OA.ProtoOAApplicationAuthReq()
    req.clientId = CLIENT_ID
    req.clientSecret = CLIENT_SECRET
    deferred = client.send(req)
    deferred.addCallbacks(on_app_auth_res, onError)

def disconnected(client, reason):
    print("❌ Disconnected:", reason)

def onMsg(client, message):
    pass  # not needed here

# === Start connection ===
client.setConnectedCallback(connected)
client.setDisconnectedCallback(disconnected)
client.setMessageReceivedCallback(onMsg)
client.startService()
reactor.run()
