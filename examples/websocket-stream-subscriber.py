#!/usr/bin/env python

import argparse
import asyncio
import websockets
from websocket_protocol import SubscriberProtocol

def generator(N):
    for i in range(N):
        yield True

async def main(endpoint):
    print(f"main() connecting...")
    protocol = SubscriberProtocol()
    async with websockets.connect(endpoint) as websocket:
        response = protocol.process("connected()")
        print(f"send -> {response}")
        await websocket.send(response)
        async for message in websocket:
            print(f"recv <- {message}")
            response = protocol.process(message)
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
