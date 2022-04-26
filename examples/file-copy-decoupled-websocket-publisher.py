#!/usr/bin/env python

import argparse
import simple_websocket
from filestreams import FilePublisher, FileSource
from decoupled import SubscriberProxy
from wsm import WebSocketMessenger

def main(file_path, endpoint):
    print(f"main(): file_path: {file_path} endpoint: {endpoint}")
    try:
        count = 0
        ws = simple_websocket.Client(endpoint)
        messenger = WebSocketMessenger(ws)
        publisher = FilePublisher(file_source=FileSource(file_path))
        subscriber = SubscriberProxy(publisher, messenger=messenger)
        print("main() starting receive loop...")
        while True:
            message = ws.receive()
            count += 1
            print(f"main() ws.receive({count}) message: {message}")
            subscriber.event(message)
    except (KeyboardInterrupt, EOFError, simple_websocket.ConnectionClosed):
        ws.close()

parser = argparse.ArgumentParser()
parser.add_argument('--input', type=str)
parser.add_argument('--endpoint', type=str)
args = parser.parse_args()
main(args.input, args.endpoint)
