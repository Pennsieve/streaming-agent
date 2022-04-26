import logging

class WebSocketMessenger:
    def __init__(self, ws):
        logging.debug(f"WebSocketMessenger [construct] ws: {ws}")
        self.ws = ws
        
    def __call__(self, message):
        logging.debug(f"WebSocketMessenger() [send] message: {message}")
        self.ws.send(message)
