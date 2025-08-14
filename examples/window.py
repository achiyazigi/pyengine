import pygame
from pygame import BUTTON_LEFT, Color, Rect
from pyengine import *

W = 1280
H = 720
BG = Color("Black")


class WindowsManager(Entity, metaclass=Singelton):
    def __init__(self):
        super().__init__()
        self.windows: List[Window] = []  # sorted by z_index
        self.transform.size = Size(W, H)
        InputManager().register_mouse_pressed(BUTTON_LEFT, self, self.on_mouse_pressed)
        GameManager().instatiate(self)

    def register_window(self, window: "Window"):
        z_index = Window.DEFAULT_Z_INDEX
        if len(self.windows) > 0:
            z_index = self.windows[-1].z_index + 1
        window.z_index = z_index
        self.windows.append(window)

    def unregister_window(self, window: "Window"):
        Utils.remove_from_sorted_list(self.windows, window, key=lambda w: w.z_index)

    def focus_on(self, window: "Window"):
        self.unregister_window(window)
        self.register_window(window)

    def get_focused(self):
        if len(self.windows) > 0:
            return self.windows[-1]
        return None

    def on_mouse_pressed(self):
        mouse_pos = pygame.mouse.get_pos()
        for w in reversed(self.windows):
            if w.is_minimized:
                continue
            if w.transform.rect().collidepoint(mouse_pos):
                if len(self.windows) > 1 and w != self.windows[-1]:
                    self.focus_on(w)

                if w.menu_bar.transform.rect().collidepoint(mouse_pos):
                    w.is_dragging = True
                    w.dragging_offset = Vector2(mouse_pos) - w.transform.pos
                break


class DockButton(Entity):
    MINIMIZED_OVERLAY_COLOR = Color(100, 100, 100, 128)

    def __init__(self, window: "Window"):
        super().__init__()
        self.window = window
        self.transform.size = Size(Dock.WINDOW_ICON_SIZE)
        self.icon_sur = Surface(self.transform.size)
        if window.icon:
            self.icon_sur = self.window
        else:
            self.icon_sur.fill(Dock.PLACE_HOLDER_COLOR)
            self.icon_sur.blit(window.menu_bar.title_sur, Pos())

        if (
            self.icon_sur.get_width() != self.transform.size.w
            or self.icon_sur.get_height() != self.transform.size.h
        ):
            self.icon_sur = pygame.transform.scale(self.icon_sur, self.transform.size)
        self.minimized_icon_sur = self.icon_sur.copy()
        self.minimized_icon_sur.set_alpha(128)
        InputManager().register_mouse_released(BUTTON_LEFT, self, self.on_mouse_pressed)

    def render(self, sur):
        if self.window.is_minimized:
            sur.blit(self.minimized_icon_sur, self.transform.pos)
        else:
            sur.blit(self.icon_sur, self.transform.pos)

    def on_mouse_pressed(self):
        mouse_pos = pygame.mouse.get_pos()
        if self.transform.rect().collidepoint(mouse_pos):
            if self.window.is_minimized:
                self.window.is_minimized = False
            WindowsManager().focus_on(self.window)


class Dock(Entity, metaclass=Singelton):
    H = 60
    MARGIN = 5
    WINDOW_ICON_SIZE = H - MARGIN * 2
    BG = Color(100, 100, 100)
    PLACE_HOLDER_COLOR = Color(100, 150, 200)
    SELECTED_BORDER_COLOR = Color("Magenta")

    def __init__(self):
        super().__init__()
        self.windows: List[Window] = []
        self.transform.size.h = Dock.H
        self.transform.pos.y = H - Dock.H
        self.front_window = None

    def update_transform(self):
        self.transform.size.w = (
            len(self.windows) * Dock.WINDOW_ICON_SIZE
            + (len(self.windows) + 1) * Dock.MARGIN
        )
        self.transform.pos.x = (W - self.transform.size.w) / 2

    def register_window(self, window):
        self.windows.append(window)
        self.update_transform()

    def unregister_window(self, window):
        self.windows.remove(window)
        self.update_transform()

    def render(self, sur):
        focused = WindowsManager().get_focused()

        pygame.draw.rect(sur, Dock.BG, self.transform.rect())
        offset = self.transform.pos + Pos(Dock.MARGIN)
        if focused:
            self.z_index = focused.z_index + 1
        for window in self.windows:
            if window.dock_button.z_index != self.z_index + 1:
                window.dock_button.z_index = self.z_index + 1
            if focused:
                # render focused border
                if window == focused and not window.is_minimized:
                    pygame.draw.rect(
                        sur,
                        Dock.SELECTED_BORDER_COLOR,
                        Rect(
                            offset - Size(Dock.MARGIN),
                            Size(Dock.WINDOW_ICON_SIZE + Dock.MARGIN * 2),
                        ),
                    )
            window.dock_button.transform.pos = offset.copy()

            offset.x += Dock.WINDOW_ICON_SIZE + Dock.MARGIN


class CloseButton(UiButton):
    def __init__(self, pos, size, window: "Window"):
        super().__init__()
        self.transform.pos = pos
        self.transform.size = size
        self.window = window
        self.text = "X"

    def on_left_click(self):
        super().on_left_click()
        GameManager().destroy(self.window)

    def render(self, sur):
        pass

    def managed_render(self, sur: Surface):
        super().render(sur)


class MinimizeButton(UiButton):
    def __init__(self, pos, size, window: type["Window"]):
        super().__init__()
        self.transform.pos = pos
        self.transform.size = size
        self.window = window
        self.text = "-"

    def on_left_click(self):
        super().on_left_click()
        self.window.is_minimized = True

    def render(self, sur):
        pass

    def managed_render(self, sur: Surface):
        super().render(sur)


class MenuBar(Entity):
    H = 30
    BUTTON_WIDTH = 20
    COLOR = Color(200, 200, 200)

    def __init__(self, pos: Pos, width: int, window: type["Window"]):
        super().__init__()
        self.transform.pos = pos
        self.transform.size = Size(width, MenuBar.H)
        self.close_button = GameManager().instatiate(
            CloseButton(
                Pos(
                    self.transform.rect().right - MenuBar.BUTTON_WIDTH,
                    self.transform.pos.y,
                ),
                Size(MenuBar.BUTTON_WIDTH, MenuBar.H),
                window,
            )
        )
        self.minimize_button = GameManager().instatiate(
            MinimizeButton(
                Pos(
                    self.transform.rect().right - MenuBar.BUTTON_WIDTH * 2,
                    self.transform.pos.y,
                ),
                Size(MenuBar.BUTTON_WIDTH, MenuBar.H),
                window,
            )
        )
        self.window = window
        self.close_button.set_parent(self.window)
        self.minimize_button.set_parent(self.window)
        self.title_sur = GameManager().font.render(
            self.window.title, True, Window.TITLE_COLOR
        )

    def start(self):
        super().start()
        self.close_button.update_order = self.update_order + 1
        self.minimize_button.update_order = self.update_order + 1

    def managed_render(self, sur: Surface):
        pygame.draw.rect(sur, MenuBar.COLOR, self.transform.rect())
        sur.blit(self.title_sur, self.transform.pos)
        self.close_button.managed_render(sur)
        self.minimize_button.managed_render(sur)

    def kill(self):
        super().kill()
        GameManager().destroy(self.close_button)


class Window(Entity):
    BG = Color(150, 150, 150)
    TITLE_COLOR = Color(30, 30, 30)
    DEFAULT_Z_INDEX = 0
    BORDER_COLOR = Color(80, 80, 80)
    BORDER_THICKNESS = 2

    def __init__(
        self,
        title: str,
        size: Size,
        pos: Pos | None = None,
        icon: Surface | None = None,
    ):
        super().__init__()
        self.title = title
        if not pos:
            pos = Pos()
        self.transform.pos = pos
        self.is_minimized = False
        self.transform.size = size
        self.menu_bar = GameManager().instatiate(
            MenuBar(self.transform.pos.copy(), self.transform.size.w, self)
        )
        self.menu_bar.set_parent(self)
        self.is_dragging = False
        self.dragging_offset = Vector2()
        InputManager().register_mouse_released(
            pygame.BUTTON_LEFT, self, self.on_mouse_release
        )
        self.icon = icon
        self.dock_button = GameManager().instatiate(DockButton(self))
        self.z_index = Window.DEFAULT_Z_INDEX

        Dock().register_window(self)
        WindowsManager().register_window(self)

    def start(self):
        super().start()
        self.menu_bar.update_order = self.update_order + 1

    def on_mouse_release(self):
        self.is_dragging = False

    def update(self, dt):
        super().update(dt)
        if self.is_dragging:
            mouse_pos = Vector2(pygame.mouse.get_pos())
            self.transform.pos = mouse_pos - self.dragging_offset

    def render(self, sur):
        if self.is_minimized:
            return
        pygame.draw.rect(sur, Window.BG, self.transform.rect())
        self.menu_bar.managed_render(sur)
        pygame.draw.lines(
            sur,
            Window.BORDER_COLOR,
            True,
            [
                self.transform.rect().topleft,
                self.transform.rect().topright,
                self.transform.rect().bottomright - Size(0, Window.BORDER_THICKNESS),
                self.transform.rect().bottomleft - Size(0, Window.BORDER_THICKNESS),
            ],
            Window.BORDER_THICKNESS,
        )

    def kill(self):
        super().kill()
        GameManager().destroy(self.menu_bar, self.dock_button)
        Dock().unregister_window(self)
        WindowsManager().unregister_window(self)


def main():
    chrome_w = GameManager().instatiate(Window("Chrome", Size(640, 520)))
    code_w = GameManager().instatiate(Window("Code", Size(340, 220), Pos(500, 500)))
    files_w = GameManager().instatiate(Window("Files", Size(100, 70), Pos(10, 500)))
    bin_w = GameManager().instatiate(Window("Bin", Size(70, 220), Pos(500, 100)))
    bin_w.is_minimized = True

    GameManager().instatiate(Dock())
    pygame.init()
    pygame.display.set_caption("Window")
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
