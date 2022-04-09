#!/usr/bin/env python

import argparse
import asyncio
from filestreams import FilePublisher
from edfstreams import EdfFileSource
from proxy import SubscriberProxy

async def main(input, endpoint):
    print("main(): starting...")
    publisher = FilePublisher(file_source=EdfFileSource(input))
    subscriber = SubscriberProxy(publisher)
    await subscriber.connect(endpoint)
    print("main(): running/waiting...")
    await asyncio.Future()  # run forever

parser = argparse.ArgumentParser()
parser.add_argument('--input', type=str)
parser.add_argument('--endpoint', type=str)
args = parser.parse_args()
asyncio.run(main(args.input, args.endpoint))
