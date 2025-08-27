import math

from pygame import Color
import pygame
from pyengine import *

W = 640
H = 512
BG = Color("Black")


class ProgressBar(Entity):
    BGCOLOR = pygame.Color(200, 0, 0)
    FCOLOR = pygame.Color(0, 200, 0)
    TEXT_COLOR = pygame.Color(255, 255, 255)

    def __init__(
        self,
        initial_value: float,
        size: Size = Size(),
        pos: Pos = Pos(),
        max_value: float = 1,
        min_value=0,
        name="",
    ):
        super().__init__()
        assert min_value <= initial_value <= max_value
        self.initial_value = initial_value
        self.value = initial_value
        self.max_value = max_value
        self.min_value = min_value
        self.range = max_value - min_value
        self.transform.pos = pos
        self.transform.size = size
        self.edge_thickness = math.ceil(size.h / 6)
        self.name = name
        font = pygame.font.Font(
            size=int(self.transform.size.h - self.edge_thickness * 2),
        )
        self.text_sur = font.render(self.name, True, ProgressBar.TEXT_COLOR)
        self.z_index = -1

    def render(self, sur):
        pygame.draw.rect(sur, ProgressBar.BGCOLOR, self.transform.rect())
        precentage = (
            (self.value - self.min_value) / self.range if self.range != 0 else 0
        )
        bar_w = (self.transform.size.w - self.edge_thickness * 2) * precentage
        bar_h = self.transform.size.h - self.edge_thickness * 2
        pygame.draw.rect(
            sur,
            ProgressBar.FCOLOR,
            pygame.Rect(
                self.transform.pos.x + self.edge_thickness,
                self.transform.pos.y + self.edge_thickness,
                bar_w,
                bar_h,
            ),
        )
        sur.blit(self.text_sur, self.transform.pos + Size(self.edge_thickness))


def main():
    GameManager().instatiate(ProgressBar(1, Size(W / 3, 50), Pos(), 1.5, 0, "progress"))
    pygame.init()
    pygame.display.set_caption("Progress Bar")
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
