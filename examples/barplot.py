from math import ceil, log
import pygame
from pygame import Color
from pyengine import *

W = 640
H = 512
BG = Color("Black")


class BarPlot(Animation):
    AXIS_COLOR = Color(100, 100, 100)
    BAR_DEFAULT_COLOR = Color(245, 154, 0, 255)
    LABEL_COLOR = Color("White")
    BAR_X_PAD = 10
    ANIMATION_DUR_SECS = 3
    Y_TICS_COUNT = 10

    def __init__(
        self,
        pos: Pos,
        size: Size,
        ys: List[float],
        xs: List[str | float] = None,
        title: str = "",
    ):
        super().__init__(BarPlot.ANIMATION_DUR_SECS, AnimationType.EaseOutElastic)
        self.transform.pos = pos
        self.transform.size = size
        self.ys = ys
        if xs == None:
            xs = [""] * len(self.ys)
        self.xs = [str(x) for x in xs]
        self.max_value = max(self.ys)
        self.min_value = min(self.ys)
        self.scale_factor = self.transform.size.h / (
            self.max_value - (self.min_value if self.min_value < 0 else 0)
        )
        self.axis_color = BarPlot.AXIS_COLOR
        self.zero = self.transform.rect().bottom
        if self.min_value < 0:
            self.zero += self.min_value * self.scale_factor
        self.bar_width = (
            self.transform.size.w - (len(self.ys) + 1) * BarPlot.BAR_X_PAD
        ) / len(self.ys)
        self.animation_stretch = 0

        self.hovered_bar_idx = None

        title_font = pygame.font.Font(size=int(self.transform.size.h / 7))
        self.title_sur = title_font.render(title, True, BarPlot.LABEL_COLOR)

        self.details_h = self.transform.size.h / 5
        details_title_h = int(self.details_h / 3)
        details_value_h = int(self.details_h - details_title_h)
        self.details_title_font = pygame.font.Font(size=details_title_h)
        self.details_value_font = pygame.font.Font(size=details_value_h)

    def bar_idx_from_pos(self, pos: Pos):
        res = (pos.x - self.transform.pos.x) / (BarPlot.BAR_X_PAD + self.bar_width)
        idx = int(res)
        if 0 <= idx < len(self.ys):
            y = self.ys[idx]
            h = abs(y * self.scale_factor) * self.animation_stretch
            top = self.zero - h
            if y < 0:
                top = self.zero
            bottom = top + h
            if top < pos.y < bottom:
                return int(res)
        return None

    def draw_axis(self, sur: Surface):
        pygame.draw.line(
            sur,
            self.axis_color,
            Pos(self.transform.pos.x, self.zero),
            Pos(
                self.transform.rect().right,
                self.zero,
            ),
            2,
        )

        for tic_index in range(BarPlot.Y_TICS_COUNT):
            tic_y = (
                self.transform.pos.y
                + tic_index * self.transform.size.h / BarPlot.Y_TICS_COUNT
            )

            tic_label = f"{(self.zero - tic_y) / self.scale_factor:.2f}"
            pygame.draw.line(
                sur,
                self.axis_color,
                Pos(self.transform.pos.x, tic_y),
                Pos(
                    self.transform.rect().right,
                    tic_y,
                ),
            )
            tic_label_sur = GameManager().font.render(tic_label, False, self.axis_color)
            sur.blit(
                tic_label_sur,
                Pos(self.transform.pos.x, tic_y - tic_label_sur.get_height() / 2),
            )

    def animation_frame(self, x):
        super().animation_frame(x)
        self.animation_stretch = x

    def update(self, dt):
        super().update(dt)
        self.zero = self.transform.rect().bottom
        if self.min_value < 0:
            self.zero += self.min_value * self.scale_factor
        mouse_pos = Pos(pygame.mouse.get_pos())
        self.hovered_bar_idx = self.bar_idx_from_pos(mouse_pos)

    def draw_details(self, sur: Surface, x: str, y: float):
        origin = Pos(pygame.mouse.get_pos())
        title_sur = self.details_title_font.render(x, True, BarPlot.LABEL_COLOR)
        value_sur = self.details_value_font.render(
            f"{y:.4f}".rstrip("0").rstrip("."), True, BarPlot.LABEL_COLOR
        )
        details_w = max(title_sur.get_width(), value_sur.get_width())
        origin.x -= details_w / 2
        origin.x = pygame.math.clamp(
            origin.x, self.transform.pos.x, self.transform.rect().right - details_w
        )
        origin.y = pygame.math.clamp(
            origin.y - self.details_h,
            self.transform.pos.y,
            self.transform.rect().bottom - self.details_h,
        )
        sur.blit(title_sur, origin)
        sur.blit(value_sur, origin + Size(0, title_sur.get_height()))

    def render(self, sur):
        super().render(sur)
        self.draw_axis(sur)
        left = self.transform.pos.x
        for x, y in zip(self.xs, self.ys):
            left += BarPlot.BAR_X_PAD

            h = abs(y * self.scale_factor) * self.animation_stretch
            top = self.zero - h
            if y < 0:
                top = self.zero

            bar_rect = Rect(Pos(left, top), Size(self.bar_width, h))
            bar_label_sur = GameManager().font.render(x, True, BarPlot.LABEL_COLOR)
            bar_label_rect = bar_label_sur.get_rect()
            if bar_label_rect.w > self.bar_width and self.bar_width < h:
                if bar_label_rect.h > self.bar_width:
                    bar_label_sur = pygame.transform.scale(
                        bar_label_sur,
                        Vector2(bar_label_rect.size)
                        * self.bar_width
                        / bar_label_rect.h,
                    )
                bar_label_sur = pygame.transform.rotate(bar_label_sur, 90)
                bar_label_rect = bar_label_sur.get_rect()
            bar_label_rect.center = bar_rect.center
            pygame.draw.rect(
                sur,
                BarPlot.BAR_DEFAULT_COLOR,
                bar_rect,
            )
            sur.blit(bar_label_sur, bar_label_rect)
            left += self.bar_width
        if self.hovered_bar_idx != None:
            self.draw_details(
                sur, self.xs[self.hovered_bar_idx], self.ys[self.hovered_bar_idx]
            )
        sur.blit(self.title_sur, self.transform.pos)


def main():
    GameManager().instatiate(
        BarPlot(
            Pos(),
            Size(W, H / 2),
            [
                13.89,
                14.44,
                16.11,
                19.44,
                22.22,
                25.56,
                27.78,
                28.33,
                22.78,
                19.44,
                14.44,
                10.56,
                15.05,
                15.05,
                16.5,
                19.65,
                24.25,
                25.25,
                28.55,
                29.25,
                27.0,
                24.4,
                21.0,
                15.8,
                12.25,
                13.75,
                13.5,
                20.8,
                22.9,
                26.0,
                27.9,
                28.6,
                27.15,
                24.8,
                20.4,
                18.05,
            ],
            [
                "Jan 2020",
                "Feb 2020",
                "Mar 2020",
                "Apr 2020",
                "May 2020",
                "Jun 2020",
                "Jul 2020",
                "Aug 2020",
                "Sep 2020",
                "Oct 2020",
                "Nov 2020",
                "Dec 2020",
                "Jan 2021",
                "Feb 2021",
                "Mar 2021",
                "Apr 2021",
                "May 2021",
                "Jun 2021",
                "Jul 2021",
                "Aug 2021",
                "Sep 2021",
                "Oct 2021",
                "Nov 2021",
                "Dec 2021",
                "Jan 2022",
                "Feb 2022",
                "Mar 2022",
                "Apr 2022",
                "May 2022",
                "Jun 2022",
                "Jul 2022",
                "Aug 2022",
                "Sep 2022",
                "Oct 2022",
                "Nov 2022",
                "Dec 2022",
            ],
            "Weather in Israel",
        ),
        BarPlot(
            Pos(0, H / 2),
            Size(W, H / 2),
            [
                1441719852.0,  # India
                1425178500.0,  # China
                341814420.0,  # United States
                279476311.0,  # Indonesia
                245209815.0,  # Pakistan
                229152220.0,  # Nigeria
                216422446.0,  # Brazil
                83294633.0,  # Germany
                26620593.0,  # Australia
                9227652.0,  # Israel
            ],
            [
                "India",
                "China",
                "United States",
                "Indonesia",
                "Pakistan",
                "Nigeria",
                "Brazil",
                "Germany",
                "Australia",
                "Israel",
            ],
            "Population",
        ),
    )
    pygame.init()
    pygame.display.set_caption("Bar Plot")
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
