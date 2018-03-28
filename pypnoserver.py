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
WIDTH, HEIGHT = 490, 490

ACTIONS = {
    'left': lambda pos: (max(0, pos[0] - STEPSIZE), pos[1]),
    'right': lambda pos: (min(WIDTH, pos[0] + STEPSIZE), pos[1]),
    'up': lambda pos: (pos[0], max(0, pos[1] - STEPSIZE)),
    'down': lambda pos: (pos[0], min(HEIGHT, pos[1] + STEPSIZE)),
}

MESSAGE_ACTIONS = dict(zip(map(bin, range(20)), ACTIONS.keys()))


class Game(object):

    def __init__(self):
        self.players = {}
        self.loop = asyncio.get_event_loop()
        self.player_id = 0

    async def connect(self, websocket, path):
        self.player_id += 1
        self.players[websocket] = {
            'id': self.player_id,
            'pos': [random.randint(0, WIDTH), random.randint(0, HEIGHT)]
        }
        cors = [self.consumer(websocket), self.producer()]
        try:
            done, pending = await asyncio.wait(cors, return_when=asyncio.FIRST_COMPLETED)
            for task in pending:
                task.cancel()
        finally:
            del self.players[websocket]
            print('player quit')

    async def consumer(self, websocket):
        while websocket.open:
            async for message in websocket:
                await self.consume(websocket, message)
                await asyncio.sleep(.01)

    async def producer(self):
        while True:
            state = self.get_state()
            await asyncio.wait([ws.send(state) for ws in self.players])
            print(f'sent: {state}')
            await asyncio.sleep(.1)

    async def consume(self, websocket, message):
        pos = self.players[websocket]['pos']
        action = MESSAGE_ACTIONS[message]
        print(f'{id(websocket)}: {action}')
        self.players[websocket]['pos'] = ACTIONS[action](pos)

    def get_state(self):
        return '|'.join(f'{v["id"]},' + ','.join(map(str, v['pos'])) for v in self.players.values())

if __name__ == '__main__':
    game = Game()
    try:
        ws_server = websockets.serve(
            game.connect,
            os.environ['server_private_ip'],
            os.environ['server_ws_port']
        )
        asyncio.get_event_loop().run_until_complete(ws_server)
        asyncio.get_event_loop().run_forever()
    except KeyboardInterrupt:
        pass
    except Exception as e:
        raise e