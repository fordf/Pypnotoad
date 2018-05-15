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
import numpy as np
from queue import PriorityQueue
from collections import OrderedDict, defaultdict

from playermap import npPlayerMap


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


class Game:
    """Async communicator and calculator in chief."""

    def __init__(self):
        self.players = {}
        self.player_map = npPlayerMap()
        self.state_id = 0
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
        player = OrderedDict((
            ('id', self.player_id),
            ('websocket', websocket),
            ('xy', (10, 10)),
            ('facing', random.choice(range(4))),
            # ('licking', False),
        ))
        self.players[self.player_id] = player
        self.player_map.add(player)
        self.state_id = self.state_id + 1 % 5000
        cors = [self.consumer(player), self.producer(player)]
        try:
            # send player their own initial data
            await websocket.send(self.encode_state(player))
            print('Sent initial')
            # set up tasks to consume and send data
            done, pending = await asyncio.wait(cors, return_when=asyncio.FIRST_COMPLETED)
            for task in pending:
                task.cancel()
        except Exception as e:
            print(e)
        finally:
            del self.players[player['id']]
            self.player_map.remove(player['id'])
            print('player quit')

    async def producer(self, player):
        state_id = -1
        while True:
            await asyncio.sleep(.1)
            if self.state_id == state_id:
                continue
            state_id = self.state_id
            for iD, player in self.players.items():
                close_players = [self.players[i] for i in self.player_map.get_within_range(player)]
                print(self.encode_full_state(close_players))
                await player['websocket'].send(self.encode_full_state(close_players))
            print(f'''sent
                players: {[p['xy'] for p in self.players.values()]}
                state_id: {state_id}''')

    async def consumer(self, player):
        while player['websocket'].open:
            async for message in player['websocket']:
                await self.consume(player, message)
                await asyncio.sleep(.01)

    async def consume(self, player, message):
        action = self.actions[message]
        print(f'consumed: {player["id"]}: {action}')
        player.update(action(player))
        self.state_id = self.state_id + 1 % 5000

    def encode_full_state(self, players):
        return '|'.join(
            self.encode_state(player) for player in players
        )

    def encode_state(self, player):
        return ','.join(
            self.state_encoders.get(k, lambda x: str(x))(v)
            for k, v in player.items()
            if k != 'websocket'
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