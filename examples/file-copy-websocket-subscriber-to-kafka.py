#!/usr/bin/env python

import argparse
import asyncio
import websockets
from reactivestreams_kafka import KafkaSubscriber
from proxy import PublisherProxy

global_broker = None
global_topic = None
global_buffer_size = None

# web-socket connection handler
async def handler(websocket):
    print("handler(): starting")
    publisher = PublisherProxy()
    publisher.attach(websocket)
    subscriber = KafkaSubscriber(global_topic, broker=global_broker, buffer_size=global_buffer_size)
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
parser.add_argument('--broker', type=str, default="localhost:9092")
parser.add_argument('--topic', type=str)
parser.add_argument('--buffer-size', type=int, default=3)
args = parser.parse_args()
global_broker = args.broker
global_topic = args.topic
global_buffer_size = args.buffer_size
asyncio.run(main(args.host, args.port))
