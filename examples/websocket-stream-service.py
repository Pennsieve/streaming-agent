#!/usr/bin/env python

import argparse
import asyncio
import websockets
from websocket_protocol import PublisherProtocol, SubscriberProtocol

def generator(N):
    for i in range(N):
        yield True

async def Publisher(websocket, peer):
    source = generator(5)
    protocol = PublisherProtocol(source)

    # respond to our peer's greeting
    response = protocol.process(peer)
    print(f"send -> {response}")
    await websocket.send(response)

    # process stream of messages
    async for message in websocket:
        print(f"recv <- {message}")
        response = protocol.process(message)
        if response is not None:
            print(f"send -> {response}")
            await websocket.send(response)
        else:
            print(f"closing connection...")
            await websocket.close()

async def Subscriber(websocket, peer):
    protocol = SubscriberProtocol()

    # respond to our peer's greeting
    response = protocol.process(peer)
    print(f"send -> {response}")
    await websocket.send(response)

    # process stream of messages
    async for message in websocket:
        print(f"recv <- {message}")
        response = protocol.process(message)
        if response is not None:
            print(f"send -> {response}")
            await websocket.send(response)
        else:
            print(f"closing connection...")
            await websocket.close()

async def connected(websocket):
    print(f"connected()")
    peer = await websocket.recv()
    print(f"greetings: {peer}")
    if peer == "Publisher()":
        await Subscriber(websocket, peer)
    elif peer == "Subscriber()":
        await Publisher(websocket, peer)
    else:
        print(f"peer for {peer}: not implemented")

async def main(host, port):
    print(f"server starting at: ws://{host}:{port}")
    async with websockets.serve(connected, host, port):
        await asyncio.Future()  # run forever

parser = argparse.ArgumentParser()
parser.add_argument('--host', type=str, default="localhost")
parser.add_argument('--port', type=int, default=8765)
args = parser.parse_args()
asyncio.run(main(args.host, args.port))
