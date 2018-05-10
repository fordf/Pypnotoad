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
    K_LEFT,
    K_RIGHT,
    K_UP,
    K_DOWN,
    K_l, #lick
    #what else...
]

ACTION_MESSAGES = dict(zip(ACTIONS, map(bin, range(len(ACTIONS)))))

TILEWIDTH = 32
MAP_TILES = 100, 100
WINDOW_SIZE = 500, 500

VIEW_SIZE = 640, 640
MAPRECT = Rect(0, 0, 3200, 3200)


QUIT_KEYS = {
    QUIT,
    K_ESCAPE
}


def load_image(file):
    "loads an image, prepares it for play"
    file = os.path.join(main_dir, 'data', file)
    try:
        surface = pygame.image.load(file)
    except pygame.error:
        raise SystemExit('Could not load image "%s" %s'%(file, pygame.get_error()))
    return surface.convert()


class Frog(pygame.sprite.Sprite):
    def __init__(self, player):
        super().__init__()
        self.images = [
            pygame.image.load(os.path.join(main_dir, 'data', f)).convert_alpha()
            for f in ('frog.png', 'frog_left.png', 'frog_back.png', 'frog_right.png')
        ]
        self.facing = player['facing']
        # self.licking = player['licking']
        self.rect = self.image.get_rect()
        self.rect.x = player['xy'][0] * TILEWIDTH
        self.rect.y = player['xy'][1] * TILEWIDTH

    def move_to(self, x, y, facing):
        dx, dy = x * TILEWIDTH - self.rect.x, y * TILEWIDTH - self.rect.y
        self.rect.move_ip(dx, dy)
        self.rect = self.rect.clamp(MAPRECT)
        self.facing = facing
        # self.rect.top = self.origtop - (self.rect.left//self.bounce%2)

    @property
    def image(self):
        return self.images[self.facing]

    def neighbors(self, grid):
        """Return nearby frogs."""



class GameClient(object):
    """Produces encoded user actions, sends them to server, renders what the server sends."""

    def __init__(self, dim=VIEW_SIZE):
        self.running = True
        pygame.init()
        self.screen = pygame.display.set_mode(dim)
        self.image = load_image("battlemap.png")
        pygame.display.flip()
        pygame.event.set_allowed(None)
        pygame.event.set_allowed([QUIT, KEYDOWN])
        pygame.key.set_repeat(50, 50)
        self.playerSprites = {}
        self.playerGroup = pygame.sprite.OrderedUpdates()
        # actions = [
        #     left,
        #     right,
        #     up,
        #     down,
        #     licking,
        # ]
        # self.actions = dict(zip(map(bin, range(len(actions))), actions))
        self.state_decoders = {
            'xy': lambda strg: map(int, strg.split(',')),
            # 'licking': bool,
        }

    async def run(self):
        async with websockets.connect('ws://{}:{}'.format(
            os.environ['server_endpoint'], os.environ['server_ws_port'])
        ) as websocket:
            player_state_str = await websocket.recv()
            p = list(map(int, player_state_str.split(',')))
            self.id = p[0]
            self.view_rect = Rect(p[1] * TILEWIDTH, p[2] * TILEWIDTH, *VIEW_SIZE)
            self.screen.blit(self.image, Rect(0,0,0,0), area=self.view_rect)
            print(player_state_str, self.view_rect)
            pygame.display.flip()
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
            new = set(new_state) - set(self.playerSprites)
            gone = set(self.playerSprites) - set(new_state)
            for i in gone:
                self.playerGroup.remove(self.playerSprites[i])
                del self.playerSprites[i]
            for i in new:
                player_dict = new_state[i]
                if i not in self.playerSprites:
                    self.playerSprites[i] = Frog(player_dict)
                    self.playerGroup.add(self.playerSprites[i])
                else:
                    self.playerSprites[i].move_to(*player_dict['xy'], player_dict['facing'])
            # self.playerGroup.clear(self.screen, self.image.subsurface(self.view_rect))
            # self.view_rect.x = new_state[self.id]['xy'][0]
            # self.view_rect.y = new_state[self.id]['xy'][1]
            print(self.playerGroup)
            self.playerGroup.draw(self.screen)
            await asyncio.sleep(.03)

    async def produce_update(self, websocket):
        while self.running:
            for event in pygame.event.get():
                if event.type == QUIT or event.key in QUIT_KEYS:
                    self.running = False
                    break
                try:
                    self.scroll_view(event.key)
                    await websocket.send(
                        ACTION_MESSAGES[event.key]
                    )
                except KeyError:
                    continue
            pygame.display.update()
            await asyncio.sleep(.01)

    def scroll_view(self, direction, stages=4):
        dx = dy = 0
        screen_rect = self.screen.get_clip()
        image_w, image_h = self.image.get_size()
        cur_rect = self.view_rect.copy()
        dst_rect = screen_rect.copy()
        step_size = TILEWIDTH // stages

        def update(src, dst):
            self.screen.blit(self.image.subsurface(src), dst)
            pygame.display.update()

        if direction == K_UP:
            if self.view_rect.top > 0:
                cur_rect.h = step_size
                dst_rect.h = step_size
                for _ in range(stages):
                    self.screen.scroll(dy=step_size)
                    self.view_rect.move_ip(0, -step_size)
                    cur_rect.move_ip(0, -step_size)
                    update(cur_rect, dst_rect)
        elif direction == K_DOWN:
            if self.view_rect.bottom < image_h:
                cur_rect.h = step_size
                cur_rect.bottom = self.view_rect.bottom
                dst_rect.h = step_size
                dst_rect.bottom = screen_rect.bottom
                for _ in range(stages):
                    self.screen.scroll(dy=-step_size)
                    self.view_rect.move_ip(0, step_size)
                    cur_rect.move_ip(0, step_size)
                    update(cur_rect, dst_rect)
        elif direction == K_LEFT:
            if self.view_rect.left > 0:
                cur_rect.w = step_size
                dst_rect.w = step_size
                for _ in range(stages):
                    self.screen.scroll(dx=step_size)
                    self.view_rect.move_ip(-step_size, 0)
                    cur_rect.move_ip(-step_size, 0)
                    update(cur_rect, dst_rect)
        elif direction == K_RIGHT:
            if self.view_rect.right < image_w:
                cur_rect.w = step_size
                cur_rect.right = self.view_rect.right
                dst_rect.w = step_size
                dst_rect.right = screen_rect.right
                for _ in range(stages):
                    self.screen.scroll(dx=-step_size)
                    self.view_rect.move_ip(step_size, 0)
                    cur_rect.move_ip(step_size, 0)
                    update(cur_rect, dst_rect)


def parse_state(state):
    players = {}
    for player_state_str in state.split('|'):
        p = list(map(int, player_state_str.split(',')))
        players[p[0]] = {
            'xy': p[1:3],
            'facing': p[3],
            # 'licking': p[4],
        }
    return players


client = GameClient()

asyncio.get_event_loop().run_until_complete(client.run())
