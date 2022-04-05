#!/usr/bin/env python

import argparse
import asyncio
import websockets

def generator(N):
    for i in range(N):
        yield True

def hello():
    return "Producer()"

def goodbye():
    return "goodbye()"

def process(message, source):
    response = None
    if message == "connected()":
        response = hello()
    elif message == "subscribe()":
        response = "onSubscribe()"
    elif message == "request()":
        try:
            if next(source):
                response = "onNext()"
        except StopIteration as e:
            response = "onComplete()"
        except Exceptionn as e:
            response = "onError()"
    elif message == "cancel()":
        response == goodbye()

    return response

async def main(endpoint):
    print(f"main() connecting...")
    source = generator(5)
    async with websockets.connect(endpoint) as websocket:
        response = process("connected()", source)
        print(f"send -> {response}")
        await websocket.send(response)
        async for message in websocket:
            print(f"recv <- {message}")
            response = process(message,source)
            if response is not None:
                print(f"send -> {response}")
                await websocket.send(response)
            else:
                print(f"closing connection...")
                await websocket.close()

parser = argparse.ArgumentParser()
parser.add_argument('--endpoint', type=str, default='ws://localhost:8765')
args = parser.parse_args()
asyncio.run(main(args.endpoint))
