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
        cors = [self.consumer(websocket), self.producer()]
        tasks = map(asyncio.ensure_future, cors)
        done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
        for task in pending:
            task.cancel()
        del self.players[websocket]
        print('player quit')

    async def consumer(self, websocket):
        while websocket.open:
            async for message in websocket:
                print(message)
                self.consume(websocket, message)

    async def producer(self):
        while True:
            await asyncio.wait([ws.send(self.get_state()) for ws in self.players])
            await asyncio.sleep(1)

    def consume(self, websocket, message):
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