"""This is the toad py file."""
import pygame


class Frog(pygame.sprite.Sprite):

    def __init__(self):
        super(Frog, self).__init__()
        self.img_death = pygame.image.load("data/frog_death_3.png")
        self.img_safe = pygame.image.load("data/frog_safe.png")
        self.img_life = pygame.image.load("data/lives.png")
        self.img_forward = pygame.image.load("data/pypup.png")
        self.img_back = pygame.image.load("data/pypdown.png")
        self.img_left = pygame.image.load("data/pypleft.png")
        self.img_right = pygame.image.load("data/pypright.png")
        self.img = self.img_back
        self.rect = self.img.get_rect()
        self.lives = 4
        self.rect.x = 20
        self.rect.y = 20
        self.startpos = (self.rect.x, self.rect.y)
        self.mask = pygame.mask.from_surface(self.img)

    def draw(self):
        self.mask = pygame.mask.from_surface(self.img)
        self.move()
        # self.display_lives()
        window.blit(self.img, (self.rect.x, self.rect.y))

    def move(self):
        self.rect.move(self.rect.x, self.rect.y)
        # Ensure the player stays within the playable zone.
        self.rect.clamp_ip(pygame.Rect((0, 0), (1000, 600)))

    def left(self):
        self.img = self.img_left
        self.rect.x -= 18

    def right(self):
        self.img = self.img_right
        self.rect.x += 18

    def forward(self):
        self.img = self.img_forward
        self.rect.y -= 25

    def back(self):
        self.img = self.img_back
        self.rect.y += 25

    # def display_lives(self):
    #     "Draw the life bar"
    #     x, y = 0, 40
    #     for _ in range(self.lives):
    #         window.blit(self.img_life, (x, y))
    #         x += 20

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

