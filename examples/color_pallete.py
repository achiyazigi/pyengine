import pygame
from pygame import Color
import subprocess
from pyengine import *
import shutil

W = 520
H = 480
BG = Color(0, 0, 0)


class ColorPalette(Entity):

    def __init__(self, pos: Pos, size: Size, on_pick: Callable[[Color], None] = None):
        super().__init__()

        self.transform.pos = pos
        self.transform.size = size
        self.saturation_bar_transfrom = Transform()
        self.saturation_bar_transfrom.size = Size(
            self.transform.size.w / 10, self.transform.size.h
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
        self.on_pick = on_pick
        self.z_index = 2
        self.preview_rect = Rect((0, 0), self.palette_transform.size / 10)
        self.redraw_palette()

        for y in range(int(self.saturation_bar_transfrom.size.h)):
            s = int(255 * (y / self.palette_transform.size.h))
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

        self.hovered_pos = None
        self.saturation_clicked_pos = None
        InputManager().register_mouse_released(
            pygame.BUTTON_LEFT, self, self.on_mouse_release
        )
        InputManager().register_mouse_pressed(
            pygame.BUTTON_LEFT, self, self.on_mouse_pressed
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

        color = self.get_hovered_color()
        if color and self.on_pick:
            self.on_pick(color)
        return True  # stop propegation

    def on_mouse_pressed(self):
        color = self.get_hovered_color()
        if not color and not self.saturation_bar_transfrom.rect().collidepoint(
            pygame.mouse.get_pos()
        ):
            GameManager().destroy(self)

    def get_hovered_color(self):
        if self.hovered_pos:
            if self.palette_transform.rect().collidepoint(self.hovered_pos):
                offset_pos = self.hovered_pos - self.palette_transform.pos
                return self.palette.get_at((int(offset_pos.x), int(offset_pos.y)))
        return None

    def update(self, dt):
        super().update(dt)
        mouse_pos = pygame.mouse.get_pos()
        if self.palette_transform.rect().collidepoint(mouse_pos):
            self.hovered_pos = Pos(mouse_pos)
        else:
            self.hovered_pos = None

    def render_debug(self, sur):
        super().render_debug(sur)
        if self.hovered_pos:
            pygame.draw.circle(sur, Color("Red"), self.hovered_pos, 3)

    def render(self, sur):
        sur.blit(self.palette, self.palette_transform.pos)
        sur.blit(self.saturation_bar, self.saturation_bar_transfrom.pos)
        if self.hovered_pos:
            color = self.get_hovered_color()
            self.preview_rect.center = self.hovered_pos
            pygame.draw.rect(sur, color, self.preview_rect)
            pygame.draw.rect(sur, Color("Black"), self.preview_rect, 2)

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
    GameManager().instatiate(
        ColorPalette(Pos(0, 0), Size(W, H), lambda c: print("Color" + c.__str__()))
    )

    while not GameManager().should_exit:

        GameManager().update()
        GameManager().render(display)

        # flip() the display to put your work on screen
        pygame.display.flip()


if __name__ == "__main__":
    main()
    pygame.quit()
