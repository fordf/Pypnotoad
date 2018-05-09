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
from queue import PriorityQueue
from collections import OrderedDict, defaultdict


TILES_X, TILES_Y = 100, 100

def left(player):
    return {
        'xy': (max(0, player['xy'][0] - 1), player['xy'][1]),
        'facing': 1
    }

def right(player):
    return {
        'xy': (min(TILES_X, player['xy'][0] + 1), player['xy'][1]),
        'facing': 3
    }

def up(player):
    return {
        'xy': (player['xy'][0], max(0, player['xy'][1] - 1)),
        'facing': 0
    }

def down(player):
    return {
        'xy': (player['xy'][0], min(TILES_Y, player['xy'][1] + 1)),
        'facing': 2
    }

# def lick(player):
#     return {'licking': True}


class Game(object):
    """Async communicator and calculator in chief."""

    def __init__(self):
        self.players = {}
        self.loop = asyncio.get_event_loop()
        self.player_id = 0
        actions = [
            left,
            right,
            up,
            down,
            # lick,
        ]
        self.actions = dict(zip(map(bin, range(len(actions))), actions))
        self.state_encoders = {
            'xy': lambda xy: f'{xy[0]},{xy[1]}'
        }

    async def connect(self, websocket, path):
        self.player_id += 1
        self.players[websocket] = OrderedDict((
            ('id', self.player_id),
            ('xy', (random.randint(0, TILES_X - 1),
                    random.randint(0, TILES_Y - 1))),
            ('facing', random.choice(range(4))),
            # ('licking', False),
        ))
        cors = [self.consumer(websocket), self.producer()]
        try:
            # send player their own initial data
            await websocket.send(self.encode_state(self.players[websocket]))
            print('Sent initial')
            # set up tasks to consume and send data
            done, pending = await asyncio.wait(cors, return_when=asyncio.FIRST_COMPLETED)
            for task in pending:
                task.cancel()
        except Exception as e:
            import pdb; pdb.set_trace()
            print(e)
        finally:
            del self.players[websocket]
            print('player quit')

    async def producer(self):
        while True:
            state = self.encode_full_state()
            await asyncio.wait([ws.send(state) for ws in self.players])
            print(f'sent: {state}')
            await asyncio.sleep(.1)

    async def consumer(self, websocket):
        while websocket.open:
            async for message in websocket:
                await self.consume(websocket, message)
                await asyncio.sleep(.01)

    async def consume(self, websocket, message):
        action = self.actions[message]
        player = self.players[websocket]
        print(f'{id(websocket)}: {action}')
        self.players[websocket].update(action(player))

    def encode_full_state(self):
        return '|'.join(
            self.encode_state(player) for player in self.players.values()
        )
        return state

    def encode_state(self, player):
        return ','.join(
            self.state_encoders.get(k, lambda x: str(x))(v)
            for k, v in player.items()
        )


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