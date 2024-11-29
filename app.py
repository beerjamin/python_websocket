#!/usr/bin/env python

import asyncio

from websockets.asyncio.server import serve

async def handler(websocket):
    while True:
        message = await websocket.recv()
        print(message)
        await websocket.send("Not much friend")


async def main():
    async with serve(handler, "localhost", 5000):
        await asyncio.get_running_loop().create_future()  # run forever


if __name__ == "__main__":
    asyncio.run(main())