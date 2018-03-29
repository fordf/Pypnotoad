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

QUIT_KEYS = {K_ESCAPE}

WIDTH, HEIGHT = 500, 500

COLORS = ['White', 'Red', 'Blue', 'Green', 'Pink']


def clear_callback(surf, rect):
    surf.fill((0, 0, 0), rect)


class Block(pygame.sprite.Sprite):

    def __init__(self, color, x, y):
       # Call the parent class (Sprite) constructor
       super().__init__()
       self.image = pygame.Surface([10, 10])
       self.image.fill(pygame.Color(color))
       self.rect = pygame.Rect((x, y, 10, 10))


class GameClient(object):

    def __init__(self, dim=(WIDTH, HEIGHT)):
        self.running = True
        self.screen = pygame.display.set_mode(dim)
        bg = pygame.image.load("data/background.png")
        self.bg_surface = pygame.transform.scale(bg, (800, 800)).convert()
        pygame.event.set_allowed(None)
        pygame.event.set_allowed([QUIT, KEYDOWN])
        pygame.key.set_repeat(50, 50)
        self.playerSprites = {}
        self.playerGroup = pygame.sprite.OrderedUpdates()

    async def run(self):
        clock = pygame.time.Clock()
        tickspeed = 30
        async with websockets.connect('ws://{}:{}'.format(
            os.environ['server_endpoint'], os.environ['server_ws_port'])
        ) as websocket:
            consumer_task = asyncio.ensure_future(self.consume_state(websocket))
            producer_task = asyncio.ensure_future(self.produce_update(websocket))
            done, pending = await asyncio.wait(
                [consumer_task, producer_task],
                return_when=asyncio.FIRST_COMPLETED,
            )
            for task in pending:
                task.cancel()
            pygame.quit()

    async def consume_state(self, websocket):
        while self.running:
            new_state = parse_state(await websocket.recv())
            new = set(new_state) - set(self.playerSprites)
            gone = set(self.playerSprites) - set(new_state)
            for i in gone:
                self.playerGroup.remove(self.playerSprites[i])
                del self.playerSprites[i]
            for i, pos in new_state.items():
                if i not in self.playerSprites:
                    self.playerSprites[i] = Block(COLORS[i], *pos)
                    self.playerGroup.add(self.playerSprites[i])
                else:
                    self.playerSprites[i].rect.x = pos[0]
                    self.playerSprites[i].rect.y = pos[1]
            self.playerGroup.clear(self.screen, clear_callback)
            self.playerGroup.draw(self.screen)
            await asyncio.sleep(.03)


    async def produce_update(self, websocket):
        while self.running:
            for event in pygame.event.get():
                if event.type == QUIT or event.key == QUIT:
                    self.running = False
                    break
                await websocket.send(
                    ACTION_MESSAGES[KEY_BINDINGS[event.key]]
                )
                print(ACTION_MESSAGES[KEY_BINDINGS[event.key]])
                pygame.event.clear(KEYDOWN)
            pygame.display.update()
            await asyncio.sleep(.01)


def parse_state(state):
    return {i: (x, y) for i, x, y in [map(int, p.split(',')) for p in state.split('|')]}

client = GameClient()

asyncio.get_event_loop().run_until_complete(client.run())
