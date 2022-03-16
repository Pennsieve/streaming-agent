import socket
import asyncio
import websockets

def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

async def echo(websocket):
    async for message in websocket:
        await websocket.send(message)

async def start_stream(port_num):
    async with websockets.serve(echo, "localhost", port_num): # default is 8765
        await asyncio.Future()  # run forever