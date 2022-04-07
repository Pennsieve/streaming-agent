#!/usr/bin/env python

import argparse
import asyncio
from filestreams import FilePublisher, FileSubscriber

async def main(input, output, buffer_size=1):
    print("main(): starting...")
    publisher = FilePublisher(input)
    subscriber = FileSubscriber(output, buffer_size=buffer_size)
    publisher.subscribe(subscriber)
    print("main(): running/waiting...")
    await subscriber.notify()
    #await asyncio.Future()  # run forever

parser = argparse.ArgumentParser()
parser.add_argument('--input', type=str)
parser.add_argument('--output', type=str)
parser.add_argument('--buffer-size', type=int, default=3)
args = parser.parse_args()
asyncio.run(main(args.input, args.output, args.buffer_size))
