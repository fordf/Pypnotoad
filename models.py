"""These are models of game objects."""
import pygame
import sys
from random import choice, randrange

class StaticObstacle(pygame.sprite.Sprite):
    "Base class for all static obstacles"
    def __init__(self):
        super(StaticObstacle, self).__init__()

    def draw(self):
        window.blit(self.img, (self.rect.x, self.rect.y))


class TopGround(StaticObstacle):

    def __init__(self):
        super(TopGround, self).__init__()
        self.img = pygame.image.load("data/top_ground.png")
        self.rect = self.img.get_rect()
        self.rect.x = 0
        self.rect.y = 60
        self.mask = pygame.mask.from_surface(self.img)

class River(StaticObstacle):

    def __init__(self):
        super(River, self).__init__()
        self.img = pygame.Surface((480, 200), pygame.SRCALPHA)
        self.rect = self.img.get_rect()

    def draw(self):
        self.img.fill((255, 255, 255, 128))
        window.blit(self.img, (0, 118))


class Camper(StaticObstacle):
    "Enemies camping the safezones inside the TopGround"
    def __init__(self):
        super(Camper, self).__init__()
        self.imgs = ["data/croc.png", "data/fly.png"]
        self.img = pygame.image.load(choice(self.imgs))
        self.spawns = [420, 320, 220, 120, 20]
        self.duration = randrange(5, 11)
        self.rect = self.img.get_rect()
        self.rect.x = choice(self.spawns)
        self.rect.y = 80
        self.mask = pygame.mask.from_surface(self.img)



class MovingObstacle(pygame.sprite.Sprite):
    "Base class for all moving obstacles"
    def __init__(self, x, y, img, direction):
        super(MovingObstacle, self).__init__()
        self.speed = 2
        self.go_left = direction
        self.img = pygame.image.load(img)
        self.rect = self.img.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.mask = pygame.mask.from_surface(self.img)

    def draw(self):
        "Moves and then draws the obstacle"
        # Adjust the position of the obstacle.
        if self.go_left:
            self.rect.x -= self.speed
        else:
            self.rect.x += self.speed
        # Reset the object if it moves out of screen.
        if isinstance(self, Car):
            if self.rect.x > 480:
                self.rect.x = -40
            elif self.rect.x < -40:
                self.rect.x = 480
        else:
            # To accommodate the big logs and introduce gaps, we use -180 here.
            if self.rect.x > 480:
                self.rect.x = -180
            elif self.rect.x < -180:
                self.rect.x = 480

        # And finally draw it.
        window.blit(self.img, (self.rect.x, self.rect.y))


class Car(MovingObstacle):

    def __init__(self, x, y, img, direction=0):
        super(Car, self).__init__(x, y, img, direction)


class Turtle(MovingObstacle):

    def __init__(self, x, y, img, direction=0):
        super(Turtle, self).__init__(x, y, img, direction)


class Log(MovingObstacle):

    def __init__(self, x, y, img, direction=0):
        super(Log, self).__init__(x, y, img, direction)


class Frog(pygame.sprite.Sprite):

    def __init__(self):
        super(Frog, self).__init__()
        self.img_death = pygame.image.load("data/frog_death_3.png")
        self.img_safe = pygame.image.load("data/frog_safe.png")
        self.img_life = pygame.image.load("data/lives.png")
        self.img_forward = pygame.image.load("data/frog.png")
        self.img_back = pygame.image.load("data/frog_back.png")
        self.img_left = pygame.image.load("data/frog_left.png")
        self.img_right = pygame.image.load("data/frog_right.png")
        self.img = self.img_forward
        self.rect = self.img.get_rect()
        self.lives = 4
        self.rect.x = 220
        self.rect.y = 560
        self.startpos = (self.rect.x, self.rect.y)
        self.mask = pygame.mask.from_surface(self.img)

    def draw(self):
        self.mask = pygame.mask.from_surface(self.img)
        self.move()
        self.display_lives()
        window.blit(self.img, (self.rect.x, self.rect.y))

    def move(self):
        self.rect.move(self.rect.x, self.rect.y)
        # Ensure the player stays within the playable zone.
        self.rect.clamp_ip(pygame.Rect((0, 80), (480, 520)))

    def left(self):
        self.img = self.img_left
        self.rect.x -= 20

    def right(self):
        self.img = self.img_right
        self.rect.x += 20

    def forward(self):
        self.img = self.img_forward
        self.rect.y -= 40

    def back(self):
        self.img = self.img_back
        self.rect.y += 40

    def display_lives(self):
        "Draw the life bar"
        x, y = 0, 40
        for _ in range(self.lives):
            window.blit(self.img_life, (x, y))
            x += 20

    def death(self):
        "Update lives, trigger visual clues and reset frog position to default"
        # TODO: Update lives display as soon as death occurs.
        self.lives -= 1
        self.img = self.img_death
        self.draw()
        pygame.display.flip()
        pygame.time.wait(500)
        self.rect.x, self.rect.y = self.startpos
        self.img = self.img_forward