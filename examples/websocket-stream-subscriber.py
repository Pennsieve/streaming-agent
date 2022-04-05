#!/usr/bin/env python

import argparse
import asyncio
import websockets

def process(message):
    response = None
    if message == "Producer()":
        response = "subscribe()"
    elif message == "onSubscribe()" or message == "onNext()":
        response = "request()"
    elif message == "onComplete()" or message == "onError()":
        response = "cancel()"
    elif message == "goodbye()":
        response = None
    return response

async def connected(websocket):
    print(f"connected()")
    async for message in websocket:
        print(f"recv <- {message}")
        response = process(message)
        if response is not None:
            print(f"send -> {response}")
            await websocket.send(response)
        else:
            print(f"closing connection...")
            await websocket.close()

async def main(host, port):
    print(f"server starting at: ws://{host}:{port}")
    async with websockets.serve(connected, host, port):
        await asyncio.Future()  # run forever

parser = argparse.ArgumentParser()
parser.add_argument('--host', type=str, default="localhost")
parser.add_argument('--port', type=int, default=8765)
args = parser.parse_args()
asyncio.run(main(args.host, args.port))
