import pygame
from pygame import Color
from barplot import BarPlot
from window import Window
from pyengine import *

W = 1280
H = 720
BG = Color("Black")


class WindowedBarPlot(Window):
    def __init__(self, title, size, ys: List[float], xs=None, pos=None, icon=None):
        super().__init__(title, size, pos, icon)
        self.content_rect = Rect(
            self.transform.pos + Size(0, self.menu_bar.transform.size.h),
            self.transform.size - Size(0, self.menu_bar.transform.size.h),
        )
        self.barplot = BarPlot(
            Pos(self.content_rect.topleft),
            Size(self.content_rect.size),
            ys,
            xs,
        )
        self.barplot.set_parent(self)

    def kill(self):
        super().kill()
        self.barplot.kill()

    def update(self, dt):
        super().update(dt)
        if not self.is_minimized:
            self.barplot.update(dt)

    def render(self, sur: Surface):
        super().render(sur)
        if not self.is_minimized:
            self.barplot.render(sur)

    def render_debug(self, sur):
        super().render_debug(sur)
        self.barplot.render_debug(sur)


def main():
    pygame.init()
    pygame.font.init()
    GameManager().instatiate(
        WindowedBarPlot(
            "Weather in Israel",
            Size(W - 100, H / 2),
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
            Pos(100, 0),
        ),
        WindowedBarPlot(
            "Population",
            Size(W - 100, H / 2),
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
            Pos(100, H / 2),
        ),
        WindowedBarPlot("Strike", Size(100, H), [4, 8], ["Yes", "No"]),
    )
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
