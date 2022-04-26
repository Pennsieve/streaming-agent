class WebSocketMessenger:
    def __init__(self, ws):
        print(f"WebSocketMessenger [construct] ws: {ws}")
        self.ws = ws
        
    def __call__(self, message):
        print(f"WebSocketMessenger() [send] message: {message}")
        self.ws.send(message)
