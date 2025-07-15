import pygame
from pygame import Color
from pyengine import *

W = 640
H = 512
BG = Color("Black")


class Parent(Entity):
    def __init__(self):
        super().__init__()
        self.transform.pos = Pos(W / 2, H / 2)
        self.child = GameManager().instatiate(Child())
        self.child.set_parent(self)
        self.child.transform.pos = self.transform.pos + Pos(50, 50)

    def update(self, dt):
        super().update(dt)
        self.transform.pos += Pos(1, 1)


class Child(Entity):
    def __init__(self):
        super().__init__()


def main():

    pygame.init()
    pygame.display.set_caption("pe")
    screen = pygame.display.set_mode((W, H))
    GameManager().instatiate(Parent())
    while not GameManager().should_exit:
        screen.fill(BG)
        GameManager().update()
        GameManager().render_debug(screen)
        pygame.display.flip()


if __name__ == "__main__":
    main()
    pygame.quit()
