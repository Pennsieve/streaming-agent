#!/usr/bin/env python

import argparse
import asyncio
import websockets

async def echo(websocket):
    async for message in websocket:
        #await websocket.send(message)
        print(f"message: {message}")

async def main(host, port):
    print(f"server starting at: ws://{host}:{port}")
    async with websockets.serve(echo, host, port):
        await asyncio.Future()  # run forever


parser = argparse.ArgumentParser()
parser.add_argument('--host', type=str, default="localhost")
parser.add_argument('--port', type=int, default=8765)
args = parser.parse_args()
asyncio.run(main(args.host, args.port))