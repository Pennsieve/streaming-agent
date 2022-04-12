#!/usr/bin/env python

import argparse
import asyncio
import websockets
from filestreams import FilePublisher, FileSubscriber
from proxy import PublisherProxy

global_output = None
global_buffer_size = None

# web-socket connection handler
async def handler(websocket):
    print(f"handler(): starting [websocket: {websocket}] [type: {type(websocket)}]")
    publisher = PublisherProxy()
    publisher.attach(websocket)
    subscriber = FileSubscriber(global_output, global_buffer_size)
    publisher.subscribe(subscriber)
    await subscriber.notify()
    print("handler(): finished")

async def main(host, port):
    print(f"main(): server starting at ws://{host}:{port}")
    async with websockets.serve(handler, host, port):
        await asyncio.Future()  # run forever

parser = argparse.ArgumentParser()
parser.add_argument('--host', type=str, default="localhost")
parser.add_argument('--port', type=int, default=5678)
parser.add_argument('--output', type=str)
parser.add_argument('--buffer-size', type=int, default=3)
args = parser.parse_args()
global_output = args.output
global_buffer_size = args.buffer_size
asyncio.run(main(args.host, args.port))
