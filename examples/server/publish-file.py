#!/usr/bin/env python

import argparse
import logging
import simple_websocket
from filestreams import FilePublisher, FileSource
from edfstreams import EdfFileSource
from proxy import SubscriberProxy
from wsm import WebSocketMessenger

def file_source(file_path, file_format):
    if file_format.upper() == 'EDF':
        return EdfFileSource(file_path)
    else:
        return FileSource(file_path)

def main(file_path, file_format, endpoint):
    logging.info(f"main(): file_path: {file_path} endpoint: {endpoint}")
    try:
        count = 0
        ws = simple_websocket.Client(endpoint)
        messenger = WebSocketMessenger(ws)
        publisher = FilePublisher(file_source=file_source(file_path, file_format))
        subscriber = SubscriberProxy(publisher, messenger=messenger)
        logging.debug("main() starting receive loop...")
        while True:
            message = ws.receive()
            count += 1
            logging.debug(f"main() ws.receive({count}) message: {message}")
            subscriber.event(message)
    except (KeyboardInterrupt, EOFError, simple_websocket.ConnectionClosed):
        ws.close()

parser = argparse.ArgumentParser()
parser.add_argument('--input', type=str)
parser.add_argument('--format', type=str, default='text')
parser.add_argument('--endpoint', type=str)
parser.add_argument('--log-file', type=str, default='publish-file.log')
parser.add_argument('--log-level', type=str, default='DEBUG')
args = parser.parse_args()

# initialize logging
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', 
                    filename=args.log_file,
                    level=getattr(logging, args.log_level.upper()))

main(args.input, args.format, args.endpoint)
