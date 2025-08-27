import math
from typing import List

import pygame
from pyengine import *
from progress_bar import ProgressBar
from pygame import Color

W = 640
H = 512
BG = Color("Black")


class AnimatedProgressBar(Animation):
    def __init__(
        self,
        min_value: float,
        max_value: float,
        size: Size,
        pos: Pos,
        name: str,
        duration_secs: float,
        animation_type=AnimationType.Linear,
    ):
        super().__init__(duration_secs, animation_type, True)
        self.pb = GameManager().instatiate(
            ProgressBar(0, size, pos, max_value, min_value, name)
        )
        self.transform = self.pb.transform

    def animation_frame(self, x):
        super().animation_frame(x)
        self.pb.value = x


def create_animated_progress_bar(min_value, max_value, animation_type: AnimationType):
    return AnimatedProgressBar(
        min_value,
        max_value,
        Size(W / 3, 50),
        Pos(),
        animation_type.name,
        2,
        animation_type,
    )


def stack_entities(entities: List[Entity], topleft: Pos, vertical_pad: float):
    cur = topleft.copy()
    for e in entities:
        e.transform.pos = cur.copy()
        cur.y += e.transform.size.h + vertical_pad


def main():
    stack_entities(
        GameManager().instatiate(
            create_animated_progress_bar(
                0,
                1,
                AnimationType.Linear,
            ),
            create_animated_progress_bar(
                0,
                1,
                AnimationType.Sin,
            ),
            create_animated_progress_bar(
                -0.25,
                1.25,
                AnimationType.EaseInOutBack,
            ),
            create_animated_progress_bar(
                0,
                1.5,
                AnimationType.EaseOutElastic,
            ),
            create_animated_progress_bar(
                0,
                1,
                AnimationType.EaseOutBounce,
            ),
        ),
        Pos(),
        20,
    )
    pygame.init()
    pygame.display.set_caption("Progress Bar")
    screen = pygame.display.set_mode((W, H))
    GameManager().debug = True
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
