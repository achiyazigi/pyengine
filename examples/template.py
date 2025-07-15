import pygame
from pygame import Color
from pyengine import *

W = 640
H = 512
BG = Color("Black")


def start_game_scene():
    GameManager().clear_scene()


def main():
    start_game_scene()

    pygame.init()
    pygame.display.set_caption("Template")
    screen = pygame.display.set_mode((W, H))

    UpdateManager().start_fixed_update_loop()
    while not GameManager().should_exit:
        screen.fill(BG)
        GameManager().update()
        GameManager().render(screen)
        # GameManager().render_debug(screen)
        pygame.display.flip()
    UpdateManager().stop_fixed_update_loop()


if __name__ == "__main__":
    main()
    pygame.quit()
