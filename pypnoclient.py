"""
Simple async event emitter.

Add these environment variables:
server_endpoint
server_ws_port
"""

import os
import pygame
from pygame.locals import *
import asyncio
import websockets


ACTIONS = [
    'left',
    'right',
    'up',
    'down',
]

ACTION_MESSAGES = dict(zip(ACTIONS, map(bin, range(20))))

KEY_BINDINGS = {
    K_UP: 'up',
    K_DOWN: 'down',
    K_LEFT: 'left',
    K_RIGHT: 'right',
}

WIDTH, HEIGHT = 300, 300


class GameClient(object):

    def __init__(self, dim=(WIDTH, HEIGHT)):
        self.running = True
        self.screen = pygame.display.set_mode(dim)
        bg = pygame.image.load("data/background.png")
        self.bg_surface = pygame.transform.scale(bg, (800, 800)).convert()
        self.player_image = pygame.image.load("data/frog_safe.png").convert_alpha()
        pygame.event.set_allowed(None)
        pygame.event.set_allowed([pygame.locals.QUIT,
                                  pygame.locals.KEYDOWN])
        pygame.key.set_repeat(50, 50)

    async def run(self):
        clock = pygame.time.Clock()
        tickspeed = 30
        async with websockets.connect('ws://{}:{}'.format(
            os.environ['server_endpoint'], os.environ['server_ws_port'])
        ) as websocket:
            while self.running:
                clock.tick(tickspeed)
                for event in pygame.event.get():
                    if event.type == pygame.QUIT or event.type == QUIT or event.key == QUIT:
                        self.running = False
                        break
                    await websocket.send(
                        ACTION_MESSAGES[KEY_BINDINGS[event.key]]
                    )
                    pygame.event.clear(KEYDOWN)
                pygame.display.update()

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

client = GameClient()

asyncio.get_event_loop().run_until_complete(client.run())
