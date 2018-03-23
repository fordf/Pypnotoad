"""
Simple first go at async websocket server.

Add these environment variables:
server_endpoint
server_ws_port
"""

import os
import time
import random
import asyncio
import websockets


STEPSIZE = 30

ACTIONS = {
    'left': lambda pos: (pos[0], max(0, pos[1] - STEPSIZE)),
    'right': lambda pos: (pos[0], min(300, pos[1] + STEPSIZE)),
    'up': lambda pos: (max(0, pos[0] - STEPSIZE), pos[1]),
    'down': lambda pos: (min(400, pos[0] + STEPSIZE), pos[1]),
}

MESSAGE_ACTIONS = dict(zip(map(bin, range(20)), ACTIONS.keys()))


class Game(object):

    def __init__(self):
        self.players = {}
        self.loop = asyncio.get_event_loop()

    async def connect(self, websocket, path):
        self.players[websocket] = tuple(random.randint(0, 800) for _ in range(2))
        try:
            tasks = [self.consumer_loop(websocket), self.producer_loop()]
            done, pending = await asyncio.wait(tasks)
        except websockets.exceptions.ConnectionClosed:
            for task in tasks:
                task.cancel()
            del self.players[websocket]

    async def consumer_loop(self, websocket):
        while True:
            await self.consumer(websocket)

    async def producer_loop(self):
        while True:
            await self.producer()

    async def consumer(self, websocket):
        async for message in websocket:
            await self.consume(websocket, message)

    async def producer(self):
        """Send all player positions to all players."""
        await asyncio.wait([ws.send(self.get_state()) for ws in self.players])

    async def consume(self, websocket, message):
        pos = self.players[websocket]
        action = MESSAGE_ACTIONS[message]
        print(f'{id(websocket)}: {action}')
        self.players[websocket] = ACTIONS[action](pos)

    def get_state(self):
        return '|'.join(map(str, self.players.values()))


game = Game()

ws_server = websockets.serve(
    game.connect,
    os.environ['server_private_ip'],
    os.environ['server_ws_port']
)

asyncio.get_event_loop().run_until_complete(ws_server)
asyncio.get_event_loop().run_forever()