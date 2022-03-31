#!/usr/bin/env python

import argparse
import asyncio
import websockets

async def main(endpoint):
    async with websockets.connect(endpoint) as websocket:
        try:
            while True:
                message = await websocket.recv()
                print(message)
        except Exception:
            pass
        finally:
            await websocket.close()

parser = argparse.ArgumentParser()
parser.add_argument('--endpoint', type=str)
args = parser.parse_args()
asyncio.run(main(args.endpoint))
