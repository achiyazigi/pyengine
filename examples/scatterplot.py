from math import floor
from random import random
import pygame
from pygame import Color
from pyengine import *
from typing import List, Tuple

W = 640
H = 512
BG = Color("Black")


class ScatterPlot(Entity):
    AXIS_COLOR = Color(100, 100, 100)
    SCATTER_DEFAULT_COLOR = Color(245, 154, 0, 255)
    LABEL_COLOR = Color("White")
    Y_TICS_COUNT = 10
    X_TICK_H = 10
    VALUE_FONT_SIZE = 15
    R = 3

    def __init__(
        self,
        pos: Pos,
        size: Size,
        ys: List[float],
        xs: List[float] = None,
        title: str = "",
    ):
        super().__init__()
        self.transform.pos = pos
        self.transform.size = size
        self.values_font = pygame.font.Font(size=ScatterPlot.VALUE_FONT_SIZE)

        self._ys = []
        self.ys = ys
        self.xs = xs
        self.recalculate_params_y()
        self.recalculate_params_x()
        self.axis_color = ScatterPlot.AXIS_COLOR

        title_font = pygame.font.Font(size=int(self.transform.size.h / 7))
        self.title_sur = title_font.render(title, True, ScatterPlot.LABEL_COLOR)

    def recalculate_params_x(self):
        self.max_value_x = max(self._xs) if len(self._xs) > 0 else 0
        self.min_value_x = min(self._xs) if len(self._xs) > 0 else 0
        if self.max_value_x == self.min_value_x:
            self.scale_factor_x = self.transform.size.w / (
                self.max_value_x if self.max_value_x != 0 else 1
            )
        else:
            self.scale_factor_x = self.transform.size.w / (
                self.max_value_x - self.min_value_x
            )
        self.zero_x = self.transform.rect().left
        if self.min_value_x < 0:
            self.zero_x += self.min_value_x * self.scale_factor_x
        self.x_labels_surs = {
            x: self.values_font.render(str(x), False, ScatterPlot.AXIS_COLOR)
            for x in self.xs
        }  # can be optimized rendering only new values

    def recalculate_params_y(self):
        self.max_value_y = max(self._ys) if len(self._ys) > 0 else 0
        self.min_value_y = min(self._ys) if len(self._ys) > 0 else 0
        if self.max_value_y == self.min_value_y:
            self.scale_factor_y = self.transform.size.h / (
                self.max_value_y if self.max_value_y != 0 else 1
            )
        else:
            self.scale_factor_y = self.transform.size.h / (
                self.max_value_y - self.min_value_y
            )
        self.zero_y = self.transform.rect().bottom
        if self.min_value_y < 0:
            self.zero_y += self.min_value_y * self.scale_factor_y

        self.details_h = self.transform.size.h / 2
        details_title_h = int(self.details_h / 3)
        details_value_h = int(self.details_h - details_title_h)
        self.details_title_font = pygame.font.Font(size=details_title_h)
        self.details_value_font = pygame.font.Font(size=details_value_h)

    def push_xy(self, xy: Tuple[float, float]):
        x, y = xy
        self.xs.append(x)
        self.ys.append(y)
        self.recalculate_params_x()
        self.recalculate_params_y()

    def pop_index(self, i):
        if abs(i) >= len(self.xs) or abs(i) >= len(self.ys):
            return
        x = self.xs.pop(i)
        y = self.ys.pop(i)
        self.recalculate_params_x()
        self.recalculate_params_y()

    @property
    def ys(self):
        return self._ys

    @ys.setter
    def ys(self, ys):
        if self.ys != ys:
            self._ys = ys
            self.recalculate_params_y()

    @ys.getter
    def ys(self):
        return self._ys

    @property
    def xs(self):
        return self._xs

    @xs.setter
    def xs(self, xs):
        if xs == None:
            self._xs = list(range(len(self._ys)))
        self._xs = xs
        self.recalculate_params_x()

    @xs.getter
    def xs(self):
        return self._xs

    def draw_axis(self, sur: Surface):
        pygame.draw.line(
            sur,
            self.axis_color,
            Pos(self.transform.pos.x, self.zero_y),
            Pos(
                self.transform.rect().right,
                self.zero_y,
            ),
            2,
        )

        for tic_index in range(ScatterPlot.Y_TICS_COUNT):
            tic_y = (
                self.transform.pos.y
                + tic_index * self.transform.size.h / ScatterPlot.Y_TICS_COUNT
            )

            tic_label = f"{(self.zero_y - tic_y) / self.scale_factor_y:.2f}"
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

    def update(self, dt):
        super().update(dt)
        self.zero_y = self.transform.rect().bottom
        if self.min_value_y < 0:
            self.zero_y += self.min_value_y * self.scale_factor_y

    def scale_x(self, x: float):
        return self.transform.pos.x + (x - self.min_value_x) * self.scale_factor_x

    def scale_y(self, y: float):
        return (
            self.transform.rect().bottom - (y - self.min_value_y) * self.scale_factor_y
        )

    def render(self, sur):
        super().render(sur)
        self.draw_axis(sur)

        for x, y in zip(self.xs, self.ys):
            scaled_x = self.scale_x(x)
            x_tic_top = self.zero_y - ScatterPlot.X_TICK_H / 2
            x_tic_bottom = x_tic_top + ScatterPlot.X_TICK_H
            pygame.draw.line(
                sur,
                ScatterPlot.AXIS_COLOR,
                Pos(scaled_x, x_tic_top),
                Pos(scaled_x, x_tic_bottom),
            )
            x_label_sur = self.x_labels_surs[x]
            sur.blit(
                x_label_sur, Pos(scaled_x - x_label_sur.get_width() / 2, x_tic_bottom)
            )
            scaled_y = self.scale_y(y)
            pygame.draw.circle(
                sur,
                ScatterPlot.SCATTER_DEFAULT_COLOR,
                Pos(scaled_x, scaled_y),
                ScatterPlot.R,
            )
        pygame.draw.lines(
            sur,
            ScatterPlot.SCATTER_DEFAULT_COLOR,
            False,
            [(self.scale_x(x), self.scale_y(y)) for x, y in zip(self.xs, self.ys)],
        )


class Spawner(Entity):
    INTERVAL_SECS = 0.5
    MAX_JUMP = 4

    def __init__(self, scatter_plot: ScatterPlot):
        super().__init__()
        self.timer = 0
        self.scatter_plot = scatter_plot

    def update(self, dt):
        super().update(dt)
        self.timer += dt
        if self.timer > Spawner.INTERVAL_SECS:
            self.timer = 0
            self.scatter_plot.pop_index(0)
            last_x = self.scatter_plot.xs[-1]
            last_y = self.scatter_plot.ys[-1]
            self.scatter_plot.push_xy(
                (last_x + 1, last_y + (random() * 2 - 1) * Spawner.MAX_JUMP)
            )


def main():
    scatter_plot = GameManager().instatiate(
        ScatterPlot(
            Pos(20),
            Size(W, H) - Size(40),
            [
                5.95,
                5.4,
                6.1,
                5.2,
                5.8,
                5.75,
                6.25,
                5.5,
                5.7,
                5.3,
                6.0,
                5.65,
                4.5,
                4.1,
                4.8,
                4.3,
                4.4,
                3.9,
                4.2,
                4.0,
                4.5,
                4.1,
                4.3,
                4.6,
                10.5,
                9.2,
                10.8,
                9.6,
                9.9,
                8.8,
                10.1,
                9.5,
                9.8,
                10.2,
                9.6,
                10.0,
                20.5,
                18.2,
                21.0,
                19.0,
                20.1,
                18.6,
                19.5,
                20.3,
                19.8,
                20.6,
                19.4,
                20.0,
                18.0,
                17.5,
                19.0,
                18.2,
                18.8,
                17.0,
                18.5,
                18.1,
                18.6,
                19.0,
                18.2,
                17.8,
                40.2,
                35.8,
                38.5,
                37.0,
                39.1,
                36.0,
                38.3,
                37.5,
                36.8,
                39.0,
                37.2,
                36.5,
                110.5,
                105.2,
                108.0,
                102.0,
                110.0,
                100.8,
                108.5,
                107.0,
                105.5,
                110.2,
                106.0,
                109.0,
                140.0,
                130.0,
                138.0,
                135.0,
                142.0,
                132.0,
                137.0,
                139.5,
                136.0,
                140.5,
                134.0,
                138.0,
                142.0,
                128.0,
                135.0,
                132.0,
                140.0,
                130.5,
                137.0,
                139.0,
            ],
            [
                1,
                2,
                3,
                4,
                5,
                6,
                7,
                8,
                9,
                10,
                11,
                12,
                13,
                14,
                15,
                16,
                17,
                18,
                19,
                20,
                21,
                22,
                23,
                24,
                25,
                26,
                27,
                28,
                29,
                30,
                31,
                32,
                33,
                34,
                35,
                36,
                37,
                38,
                39,
                40,
                41,
                42,
                43,
                44,
                45,
                46,
                47,
                48,
                49,
                50,
                51,
                52,
                53,
                54,
                55,
                56,
                57,
                58,
                59,
                60,
                61,
                62,
                63,
                64,
                65,
                66,
                67,
                68,
                69,
                70,
                71,
                72,
                73,
                74,
                75,
                76,
                77,
                78,
                79,
                80,
                81,
                82,
                83,
                84,
                85,
                86,
                87,
                88,
                89,
                90,
                91,
                92,
                93,
                94,
                95,
                96,
                97,
                98,
                99,
                100,
                101,
                102,
                103,
                104,
            ],
            "Weather in Israel",
        )
    )
    GameManager().instatiate(Spawner(scatter_plot))
    pygame.init()
    pygame.display.set_caption("Scatter Plot")
    screen = pygame.display.set_mode((W, H))
    GameManager().debug = True
    UpdateManager().start_fixed_update_loop()
    while not GameManager().should_exit:
        screen.fill(BG)
        GameManager().update()
        GameManager().render(screen)
        pygame.display.flip()
    UpdateManager().stop_fixed_update_loop()


if __name__ == "__main__":
    main()
    pygame.quit()
