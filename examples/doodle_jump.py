from random import random
import pygame
from pygame import Color, Vector2, Surface, Rect
from dataclasses import dataclass
from pyengine import *

W = 400
H = 640
BG = Color("Black")
G = 700
FPS = 70


class Camera(Entity):
    def __init__(self, target: Entity):
        super().__init__()
        self.target = target
        self.transform.size = Size(W, H)
        self.transform.center = target.transform.center
        self._offset = Vector2()

    def update(self, dt):
        if H / 2 < self.target.transform.center.y < H:
            self._offset = self.target.transform.center - self.transform.center
            self._offset.x = 0
        return super().update(dt)


class Platform(CollideEntity):
    PLATFORM_HEIGHT = 5

    @dataclass
    class RenderData:
        color: Color

    def __init__(self, pos: Pos, width, speed):
        super().__init__()
        self.transform.pos = pos
        self.transform.size = Size(width, Platform.PLATFORM_HEIGHT)
        self.speed = speed
        self.bumpness = -400
        self.render_data = Platform.RenderData(Color(192, 86, 0, 255))
        self.camera: Camera | None = None

    def fixed_update(self, fixed_dt):
        self.transform.pos.y += self.speed * fixed_dt

    def update(self, dt):
        if self.transform.pos.y > H + 300:
            GameManager().destroy(self)

    def render(self, sur: Surface):
        render_pos = self.transform.pos
        if self.camera:
            render_pos = self.transform.pos - self.camera._offset
        pygame.draw.rect(
            sur, self.render_data.color, Rect(render_pos, self.transform.size)
        )


class DangerousePlatform(Platform):
    def __init__(self, pos: Vector2, width, speed):
        super().__init__(pos, width, speed)
        self.render_data.color = Color("Red")
        self.strength = 5

    def render(self, sur: Surface):
        self.render_data.color.r = int(255 * self.strength / 5)
        return super().render(sur)

    def update(self, dt):
        if self.strength == 0:
            GameManager().destroy(self)
        else:
            super().update(dt)


class SlidingPlatform(Platform):
    def __init__(self, pos: Vector2, width, speed):
        super().__init__(pos, width, speed)
        self.render_data.color = Color("Blue")
        self.dir = 100

    def fixed_update(self, fixed_dt):
        self.transform.pos.x += self.dir * fixed_dt
        return super().fixed_update(fixed_dt)

    def update(self, dt):
        if self.transform.rect().right > W:
            self.dir = -100
        if self.transform.pos.x < 0:
            self.dir = 100
        return super().update(dt)


class BoostPlatform(Platform):
    def __init__(self, pos: Vector2, width, speed):
        super().__init__(pos, width, speed)
        self.render_data.color = Color("Magenta")
        self.bumpness *= 2


class Player(CollideEntity):

    @dataclass
    class RenderData:
        body_color: Color
        eyes_color: Color
        chance_to_blink: float = 0.2
        blinking_cycle: int = 2.5
        last_blink_time = 0
        blinking = False
        blinking_duration: int = 0.3

    class UiArrow(Entity):
        def __init__(self, player: Entity):
            super().__init__()
            self.player = player
            self.should_render = False
            self._distance_from_top = 40
            self._edge_size = 30

        def update(self, dt):
            self.should_render = self.player.transform.center.y < 0
            self._edge_size = -self.player.transform.center.y

        def render(self, sur: Surface):
            x = self.player.transform.center.x
            top = Vector2(x, self._distance_from_top)
            right = (Vector2Right() * self._edge_size).rotate(60) + top
            left = right - Vector2Right() * self._edge_size

            pygame.draw.polygon(sur, Color("White"), [top, right, left])
            pygame.draw.aalines(sur, Color("White"), True, [top, right, left])

    @classmethod
    def register_collision_functions(cls):
        return [
            CollisionData(Platform, cls._check_collision_platform),
            CollisionData(SlidingPlatform, cls._check_collision_platform),
            CollisionData(BoostPlatform, cls._check_collision_platform),
            CollisionData(DangerousePlatform, cls._check_collision_dangerouse_platform),
        ]

    @staticmethod
    def _check_collision_platform(player: CollideEntity, platform: Platform):
        if (
            player.velocity.y > 20
            and player.transform.rect().colliderect(platform.transform.rect())
            and player.transform.rect().bottom <= platform.transform.rect().bottom
        ):
            player.velocity.y = platform.bumpness

    @staticmethod
    def _check_collision_dangerouse_platform(
        player: CollideEntity, platform: DangerousePlatform
    ):
        if player.transform.rect().colliderect(platform.transform.rect()):
            if (
                player.velocity.y > 20
                and player.transform.rect().bottom <= platform.transform.rect().bottom
            ):
                # collision from bellow
                player.velocity.y = platform.bumpness
            elif player.transform.rect().top >= platform.transform.rect().top:
                print("hit")
                platform.strength -= 1
                platform.strength = max(platform.strength, 0)
                player.velocity.y = -platform.bumpness

    def __init__(self, pos: Pos, size: Size):
        super().__init__()
        self.transform.pos = pos
        self.transform.size = size
        self.render_data = Player.RenderData(
            Color(0, 204, 251, 255), Color(31, 12, 0, 255)
        )
        self.velocity = Vector2(0, 0)
        self.acceleration = Vector2(0, G)
        self.camera: Camera | None = None
        self.speed = 200

    def start(self):
        super().start()
        InputManager().register_key_down(
            pygame.K_RIGHT, self, lambda: self._set_velocity_x(self.speed)
        ).register_key_down(
            pygame.K_LEFT, self, lambda: self._set_velocity_x(-self.speed)
        ).register_key_up(
            pygame.K_RIGHT, self, lambda: self._set_velocity_x(0)
        ).register_key_up(
            pygame.K_LEFT, self, lambda: self._set_velocity_x(0)
        ).register_key_up(
            pygame.K_SPACE, self, lambda: self._set_velocity_y(-self.speed)
        )
        GameManager().instatiate(Player.UiArrow(self))

    def _set_velocity_x(self, new_velocity):
        self.velocity.x = new_velocity

    def _set_velocity_y(self, new_velocity):
        self.velocity.y = new_velocity

    def _update_render_data(self, dt):
        t = pygame.time.get_ticks()
        if self.render_data.blinking:
            if (
                t
                > self.render_data.last_blink_time
                + self.render_data.blinking_duration * 1000
            ):
                self.render_data.blinking = False
                self.render_data.last_blink_time = t
        else:
            if (
                t
                > self.render_data.last_blink_time
                + self.render_data.blinking_cycle * 1000
                and random() < self.render_data.chance_to_blink
            ):
                self.render_data.blinking = True
                self.render_data.last_blink_time = t

    def update(self, dt):
        self._update_render_data(dt)
        if self.transform.pos.y > H + 300:
            GameManager().clear_scene()
            GameManager().instatiate(GameOverScreen())

    def fixed_update(self, fixed_dt):
        self.transform.pos += self.velocity * fixed_dt
        self.velocity += self.acceleration * fixed_dt

    def render(self, sur: Surface):
        render_pos = self.transform.pos
        if self.camera:
            render_pos = self.transform.pos - self.camera._offset

        # render body
        pygame.draw.rect(
            sur, self.render_data.body_color, Rect(render_pos, self.transform.size)
        )
        # render eyes
        eye_size = self.transform.size / 5
        if self.render_data.blinking:
            eye_size.h /= 4
        left_eye_pos = Pos(
            render_pos.x
            + self.transform.size.w / 2.0
            - self.transform.size.w / 4.0
            - eye_size.w / 2.0,
            render_pos.y + self.transform.size.h / 4.0,
        )
        right_eye_pos = left_eye_pos + Pos(self.transform.size.w / 2.0, 0)
        pygame.draw.ellipse(
            sur, self.render_data.eyes_color, Rect(left_eye_pos, eye_size)
        )
        pygame.draw.ellipse(
            sur, self.render_data.eyes_color, Rect(right_eye_pos, eye_size)
        )


class Collectable(CollideEntity):
    @classmethod
    def register_collision_functions(cls) -> list[CollisionData]:
        return [CollisionData(Player, cls.check_collision)]

    @staticmethod
    def check_collision(collectable: CollideEntity, player: Player):
        v = collectable.transform.center - player.transform.center
        if (
            abs(v.x) < collectable.radius + player.transform.size.w / 2
            and abs(v.y) < collectable.radius + player.transform.size.h / 2
        ):
            print(v)
            collectable.on_collision(player)

    def __init__(self, platform: Platform):
        super().__init__()
        self.radius = 6
        self.color = Color("Yellow")
        self.platform = platform
        self.lifetime = 6

    def render(self, sur: Surface):
        pygame.draw.circle(
            sur,
            self.color,
            self.transform.center - self.platform.camera._offset,
            self.radius,
        )

    def fixed_update(self, fixed_dt):
        self.transform.center = self.platform.transform.center.copy()
        self.transform.pos.y -= self.radius * 2

    def update(self, dt):
        if self.lifetime < 0 or self.platform.state == EntityState.Destroyed:
            GameManager().destroy(self)
        self.lifetime -= dt

    def on_collision(self, player):
        GameManager().destroy(self)


class SpeedBoost(Collectable):

    def __init__(self, platform: Platform):
        super().__init__(platform)
        self.increment_amount = 80

    def on_collision(self, player: Player):
        player.speed += self.increment_amount
        return super().on_collision(player)


class PlatformSpawner(Entity):
    def __init__(self, pos: Pos = Pos()):
        super().__init__()
        self.transform.pos = pos
        self.seconds_between_spawns = 0.8
        self._last_spawn_time = 0
        self.speed = 90
        self.max_width = W / 2
        self.min_width = W / 7
        self.camera: Camera | None = None
        self.danger_platform_chance = 0.2
        self.sliding_platform_chance = 0.2
        self.boost_platform_chance = 0.1
        self.speed_boost_chance = 0.02

    def start(self):
        super().start()
        distance_between_platforms = self.seconds_between_spawns * self.speed
        num_of_first_pos_platforms = int(
            (H - self.transform.pos.y) / distance_between_platforms
        )
        for y in range(1, num_of_first_pos_platforms):
            pos_offset = Pos(random() * W, y * distance_between_platforms)
            self.instatiate_platform(pos_offset)

    def spawn(self):
        x_offset = random() * W
        self.instatiate_platform(Pos(x_offset, 0))

    def update(self, dt):
        t = pygame.time.get_ticks()
        if t > self._last_spawn_time + self.seconds_between_spawns * 1000:
            self._last_spawn_time = t
            self.spawn()
            self.speed += 0.1

    def instatiate_platform(self, pos_offset: Pos):
        random_width = self.min_width + random() * (self.max_width - self.min_width)
        platform_speed = self.speed + random() * 30
        new_platform = Platform(
            self.transform.pos + pos_offset, random_width, platform_speed
        )

        r = random()
        if (
            self.sliding_platform_chance + self.boost_platform_chance
            < r
            < self.sliding_platform_chance
            + self.danger_platform_chance
            + self.boost_platform_chance
        ):
            new_platform = DangerousePlatform(
                self.transform.pos + pos_offset, random_width, platform_speed
            )
        elif (
            self.boost_platform_chance
            < r
            < self.sliding_platform_chance + self.boost_platform_chance
        ):
            new_platform = SlidingPlatform(
                self.transform.pos + pos_offset, random_width, platform_speed
            )
        elif r < self.boost_platform_chance:
            new_platform = BoostPlatform(
                self.transform.pos + pos_offset, random_width, platform_speed
            )
        new_platform.camera = self.camera
        GameManager().instatiate(new_platform)
        r = random()
        if r < self.speed_boost_chance:
            GameManager().instatiate(SpeedBoost(new_platform))


class MenuButton(UiButton):
    def __init__(self, pos: Pos, size: Size):
        super().__init__()
        self.transform.pos = pos
        self.transform.size = size
        self.render_data.color = Color("white")
        self.render_data.color_hover = Color("Black")

    def start(self):
        super().start()
        self.render_data.font = pygame.Font(size=int(0.4 * self.transform.size.w))


class GameOverScreen(Entity):
    class RestartButton(MenuButton):
        def __init__(self, pos: Vector2, size: Size):
            super().__init__(pos, size)
            self.text = "Restart"

        def on_left_click(self):
            super().on_left_click()
            start_game_scene()

    class QuitButton(MenuButton):
        def __init__(self, pos: Vector2, size: Size):
            super().__init__(pos, size)
            self.text = "Quit"

        def on_hover(self):
            self.text = "Quit :("
            return super().on_hover()

        def on_hover_out(self):
            self.text = "Quit"
            return super().on_hover_out()

        def on_left_click(self):
            super().on_left_click()
            GameManager().should_exit = True

    @dataclass
    class RenderData:
        title_surf: Surface
        title_pos: Pos

    def __init__(self):
        super().__init__()
        self.z_index = -100
        self.font = pygame.Font(size=int(W / 8))
        title_surf = self.font.render("Game Over", True, Color("White"))

        self.render_data = GameOverScreen.RenderData(
            title_surf, Pos((W - title_surf.get_width()) / 2, H / 10)
        )
        self.restart_button = GameOverScreen.RestartButton(
            Pos(W / 2, H / 2), Size(100, 50)
        )
        self.restart_button.transform.center = self.restart_button.transform.pos.copy()
        self.restart_button.z_index = self.z_index + 1
        padding = W / 20
        self.quit_button = GameOverScreen.QuitButton(
            Pos(self.restart_button.transform.rect().bottomleft) + Pos(0, padding),
            self.restart_button.transform.size,
        )
        self.quit_button.z_index = self.restart_button.z_index

    def start(self):
        super().start()
        GameManager().instatiate(
            self.restart_button,
            self.quit_button,
        )

    def render(self, surf: Surface):
        surf.fill(Color("Red"))
        surf.blit(self.render_data.title_surf, self.render_data.title_pos)


def start_game_scene():
    GameManager().clear_scene()
    player = Player(Pos(W / 2, H / 2), Size(30, 40))
    platformSpawner = PlatformSpawner(Pos(0, 0))
    camera = Camera(player)

    player.camera = camera
    platformSpawner.camera = camera

    GameManager().instatiate(camera, player, platformSpawner)


def main():
    start_game_scene()
    pygame.init()
    screen = pygame.display.set_mode((W, H))

    GameManager().fps = 100
    UpdateManager.FIXED_DT = 0.005
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
