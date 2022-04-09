#!/usr/bin/env python

import argparse
import asyncio
from filestreams import FilePublisher
from reactivestreams_kafka import KafkaSubscriber

async def main(input, broker, topic, buffer_size):
    publisher = FilePublisher(input)
    subscriber = KafkaSubscriber(topic, broker=broker, buffer_size=buffer_size)
    publisher.subscribe(subscriber)
    await subscriber.notify()

parser = argparse.ArgumentParser()
parser.add_argument('--input', type=str)
parser.add_argument('--broker', type=str, default="localhost:9092")
parser.add_argument('--topic', type=str)
parser.add_argument('--buffer-size', type=int, default=3)
args = parser.parse_args()
asyncio.run(main(args.input, args.broker, args.topic, args.buffer_size))
