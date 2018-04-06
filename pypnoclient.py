"""
Simple async event emitter.

Add these environment variables:
server_endpoint
server_ws_port
"""

import os
import pygame
from pygame.locals import *
from pygame.transform import scale
import asyncio
import websockets


main_dir = os.path.dirname(os.path.abspath(__file__))

ACTIONS = [
    K_UP,
    K_DOWN,
    K_LEFT,
    K_RIGHT,
]

ACTION_MESSAGES = dict(zip(ACTIONS, map(bin, range(len(ACTIONS)))))

TILEWIDTH = 32
MAP_TILES = 100, 100
WINDOW_SIZE = 500, 500
MAP_SIZE = 3200, 3200

ZOOM = 1
view_size = 640, 640


QUIT_KEYS = {
    QUIT,
    K_ESCAPE
}



class GameClient(object):

    def __init__(self, dim=view_size):
        self.running = True
        pygame.init()
        self.screen = pygame.display.set_mode(dim)
        image = pygame.image.load("data/battlemap.png")
        if image.get_alpha() is None:
            self.image = image.convert()
        else:
            self.image = image.convert_alpha()
        self.view_rect = Rect(0, 0, *view_size)
        self.screen.blit(self.image, self.view_rect)
        pygame.display.flip()
        pygame.event.set_allowed(None)
        pygame.event.set_allowed([QUIT, KEYDOWN])
        pygame.key.set_repeat(50, 50)
        # self.playerSprites = {}
        # self.playerGroup = pygame.sprite.OrderedUpdates()

    async def run(self):
        async with websockets.connect('ws://{}:{}'.format(
            os.environ['server_endpoint'], os.environ['server_ws_port'])
        ) as websocket:
            cors = [self.consume_state(websocket), self.produce_update(websocket)]
            done, pending = await asyncio.wait(
                cors,
                return_when=asyncio.FIRST_COMPLETED,
            )
            for task in pending:
                task.cancel()
            pygame.quit()

    async def consume_state(self, websocket):
        while self.running:
            new_state = parse_state(await websocket.recv())
            # new = set(new_state) - set(self.playerSprites)
            # gone = set(self.playerSprites) - set(new_state)
            # for i in gone:
            #     self.playerGroup.remove(self.playerSprites[i])
            #     del self.playerSprites[i]
            # for i, pos in new_state.items():
            #     if i not in self.playerSprites:
            #         self.playerSprites[i] = Block(COLORS[i%5], *pos)
            #         self.playerGroup.add(self.playerSprites[i])
            #     else:
            #         self.playerSprites[i].rect.x = pos[0]
            #         self.playerSprites[i].rect.y = pos[1]
            # self.playerGroup.clear(self.screen, clear_callback)
            # self.playerGroup.draw(self.screen)
            await asyncio.sleep(.03)

    async def produce_update(self, websocket):
        while self.running:
            for event in pygame.event.get():
                if event.type == QUIT or event.key in QUIT_KEYS:
                    self.running = False
                    break
                try:
                    await websocket.send(
                        ACTION_MESSAGES[event.key]
                    )
                except KeyError:
                    continue
                self.scroll_view(event.key)
                pygame.event.clear(KEYDOWN)
            pygame.display.update()
            await asyncio.sleep(.01)

    def scroll_view(self, direction, stages=8):
        dx = dy = 0
        src_rect = None
        screen_rect = self.screen.get_clip()
        image_w, image_h = self.image.get_size()
        src_rect = self.view_rect.copy()
        dst_rect = screen_rect.copy()
        step_size = TILEWIDTH // stages

        def update(src, dst):
            self.screen.blit(self.image.subsurface(src), dst)
            pygame.display.update()

        if direction == K_UP:
            if self.view_rect.top > 0:
                src_rect.h = step_size
                dst_rect.h = step_size
                for _ in range(stages):
                    self.screen.scroll(dy=step_size)
                    self.view_rect.move_ip(0, -step_size)
                    src_rect.move_ip(0, -step_size)
                    update(src_rect, dst_rect)
        elif direction == K_DOWN:
            if self.view_rect.bottom < image_h:
                src_rect.h = step_size
                src_rect.bottom = self.view_rect.bottom
                dst_rect.h = step_size
                dst_rect.bottom = screen_rect.bottom
                for _ in range(stages):
                    self.screen.scroll(dy=-step_size)
                    self.view_rect.move_ip(0, step_size)
                    src_rect.move_ip(0, step_size)
                    update(src_rect, dst_rect)
        elif direction == K_LEFT:
            if self.view_rect.left > 0:
                src_rect.w = step_size
                dst_rect.w = step_size
                for _ in range(stages):
                    self.screen.scroll(dx=step_size)
                    self.view_rect.move_ip(-step_size, 0)
                    src_rect.move_ip(-step_size, 0)
                    update(src_rect, dst_rect)
        elif direction == K_RIGHT:
            if self.view_rect.right < image_w:
                src_rect.w = step_size
                src_rect.right = self.view_rect.right
                dst_rect.w = step_size
                dst_rect.right = screen_rect.right
                for _ in range(stages):
                    self.screen.scroll(dx=-step_size)
                    self.view_rect.move_ip(step_size, 0)
                    src_rect.move_ip(step_size, 0)
                    update(src_rect, dst_rect)


def parse_state(state):
    # return {i: (x, y) for i, x, y in [map(int, p.split(',')) for p in state.split('|')]}
    return

client = GameClient()

asyncio.get_event_loop().run_until_complete(client.run())
