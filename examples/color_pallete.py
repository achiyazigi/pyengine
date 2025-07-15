import pygame
from pygame import Color
import subprocess
from pyengine import *

W = 520
H = 480
BG = Color(0, 0, 0)


class ColorPalette(Entity):

    SATURATION_BAR_WIDTH = 30

    def __init__(self, pos: Pos, size: Size):
        super().__init__()
        self.transform.pos = pos
        self.transform.size = size
        self.saturation_bar_transfrom = Transform()
        self.saturation_bar_transfrom.size = Size(
            ColorPalette.SATURATION_BAR_WIDTH, self.transform.size.h
        )
        self.palette_transform = Transform()
        self.palette_transform.size = Size(
            self.transform.size.w - self.saturation_bar_transfrom.size.w,
            self.transform.size.h,
        )
        self.saturation_bar_transfrom.pos = self.transform.pos + Pos(
            self.palette_transform.size.w, 0
        )
        self.palette_transform.pos = self.transform.pos.copy()
        self.palette = pygame.Surface(self.palette_transform.size)
        self.saturation_bar = pygame.Surface(self.saturation_bar_transfrom.size)
        self.s = 1

        self.redraw_palette()

        for y in range(int(self.saturation_bar_transfrom.size.h)):
            s = 255 * (y / self.palette_transform.size.h)
            pygame.draw.line(
                self.saturation_bar,
                Color(s, s, s),
                (
                    0,
                    y,
                ),
                (
                    self.saturation_bar_transfrom.size.w,
                    y,
                ),
                1,
            )

        self.font = pygame.font.SysFont("Comic Sans MS", 30)
        self.hovered_pos = None
        self.saturation_clicked_pos = None
        InputManager().register_mouse_released(
            pygame.BUTTON_LEFT, self, self.on_mouse_release
        )

    def redraw_palette(self):
        for y in range(int(self.palette_transform.size.h)):
            for x in range(int(self.palette_transform.size.w)):
                h = (
                    x / self.palette_transform.size.w
                )  # Hue varies from 0 to 1 across the width
                v = 1 - (
                    y / self.palette_transform.size.h
                )  # Value varies from 1 to 0 down the height

                color = ColorPalette.hsv_to_rgb(h, self.s, v)
                self.palette.set_at((x, y), color)

    def on_mouse_release(self):
        mouse_pos = Pos(pygame.mouse.get_pos())
        if self.saturation_bar_transfrom.rect().collidepoint(mouse_pos):
            self.s = (
                1
                - (mouse_pos.y - self.saturation_bar_transfrom.pos.y)
                / self.saturation_bar_transfrom.size.h
            )
            self.redraw_palette()

        else:
            hovered_color_str = str(self.get_hovered_color())
            subprocess.run("pbcopy", text=True, input=hovered_color_str)
            print(f"coppied: {hovered_color_str}")

    def get_hovered_color(self):
        if self.hovered_pos:
            return self.palette.get_at(self.hovered_pos)
        return BG

    def update(self, dt):
        super().update(dt)
        mouse_pos = pygame.mouse.get_pos()
        if self.palette_transform.rect().collidepoint(mouse_pos):
            self.hovered_pos = Pos(mouse_pos)

    def render(self, sur):
        sur.blit(self.palette, self.palette_transform.pos)
        sur.blit(self.saturation_bar, self.saturation_bar_transfrom.pos)
        if self.hovered_pos:
            hovered_color = self.get_hovered_color()

            text_sur = self.font.render(
                str(hovered_color),
                False,
                Color("White"),
                hovered_color,
            )
            text_sur_pos = Pos(
                pygame.math.clamp(
                    self.hovered_pos.x,
                    self.transform.pos.x,
                    self.transform.rect().right - text_sur.width,
                ),
                pygame.math.clamp(
                    self.hovered_pos.y,
                    self.transform.pos.y,
                    self.transform.rect().bottom - text_sur.height,
                ),
            )
            sur.blit(text_sur, text_sur_pos)

    def compute_color(self, x, y):
        # Normalize x and y to a range of 0 to 1
        nx = x / (self.palette_transform.size.w - 1)
        ny = y / (self.palette_transform.size.h - 1)

        # Compute the color components
        r = int(255 * nx)  # Red increases from left to right
        g = int(255 * ny)  # Green increases from top to bottom
        b = int(255 * (1 - ny))  # Blue decreases from top to bottom

        return (r, g, b)

    # Function to convert HSV to RGB
    def hsv_to_rgb(h, s, v):
        h = h * 360  # Convert to degrees
        c = v * s
        x = c * (1 - abs((h / 60) % 2 - 1))
        m = v - c

        if 0 <= h < 60:
            r, g, b = c, x, 0
        elif 60 <= h < 120:
            r, g, b = x, c, 0
        elif 120 <= h < 180:
            r, g, b = 0, c, x
        elif 180 <= h < 240:
            r, g, b = 0, x, c
        elif 240 <= h < 300:
            r, g, b = x, 0, c
        elif 300 <= h < 360:
            r, g, b = c, 0, x
        else:
            r, g, b = 0, 0, 0

        return int((r + m) * 255), int((g + m) * 255), int((b + m) * 255)


def main():

    display = pygame.display.set_mode((W, H))
    GameManager().instatiate(ColorPalette(Pos(0, 0), Size(W, H)))

    while not GameManager().should_exit:

        GameManager().update()
        GameManager().render(display)

        # flip() the display to put your work on screen
        pygame.display.flip()


if __name__ == "__main__":
    main()
    pygame.quit()
