from math import atan2, cos
from random import randint
import pygame
from pygame import BUTTON_LEFT, Color
from pyengine import *

W = 640
H = 512
BG = Color("Black")
G = 15

from pygame.math import Vector2


def point_collide_segment(p: Vector2, lines: List[Vector2], e: float) -> bool:
    """
    Checks for collision between a point and a series of connected line segments.

    Args:
        p: The point to check for collision.
        lines: A list of Vector2 points defining the line segments.
        e: The tolerance for collision (e.g., line thickness).

    Returns:
        True if the point collides with any line segment, False otherwise.
    """
    if len(lines) < 2:
        return False

    for i in range(len(lines) - 1):
        p1 = lines[i]
        p2 = lines[i + 1]

        # Calculate the squared distance of the segment.
        # This avoids using expensive square roots.
        segment_length_sq = (p2 - p1).length_squared()

        # If the segment is a single point, check for collision with that point
        if segment_length_sq == 0:
            if (p - p1).length() <= e:
                return True
            continue

        # Calculate the projection of the point p onto the line segment.
        # This 't' value determines where the closest point on the infinite line
        # lies in relation to the segment endpoints (p1 and p2).
        t = max(0, min(1, (p - p1).dot(p2 - p1) / segment_length_sq))

        # Find the closest point on the segment to the point p.
        closest_point = p1 + t * (p2 - p1)

        # Check if the distance between p and the closest point is within the tolerance.
        if (p - closest_point).length() <= e:
            return True

    return False


def get_y_at(line: Tuple[Vector2, Vector2], x: float):
    m = (line[1].y - line[0].y) / (line[1].x - line[0].x)
    # y = mx+n => n=y-mx
    n = line[0].y - m * line[0].x
    return m * x + n


class Scroll(Entity, metaclass=Singelton):
    def __init__(self):
        super().__init__()
        GameManager().instatiate(self)

    def update(self, dt):
        super().update(dt)
        self.transform.pos.x -= Player().speed * dt


class Targets(Entity, metaclass=Singelton):
    SPAWN_INTERVAL_SECS = 4

    def __init__(self):
        super().__init__()
        self.targets: List[Target] = []
        GameManager().instatiate(self)
        self.spawn_timer = 0

    def register_target(self, target: "Target"):
        self.targets.append(target)

    def update(self, dt):
        super().update(dt)
        if self.spawn_timer > Targets.SPAWN_INTERVAL_SECS:
            self.spawn_timer = 0
            self.generate_target()
        self.spawn_timer += dt

    def generate_target(self):
        x = W
        line = Floor().get_line_for_x(x)
        self.register_target(
            GameManager().instatiate(
                Target(
                    Pos(W + 20, get_y_at(line, x) - randint(100, 400)), randint(0, 180)
                )
            )
        )


class Target(CollideEntity):
    W = 50
    THICKNESS = 5
    COLOR = Color("White")
    HIT_COLOR = Color("Green")

    def __init__(self, pos: Pos, angle_deg):
        super().__init__()
        Targets().register_target(self)
        self.vec = Vector2(Target.W, 0).rotate(angle_deg)
        self.transform.pos = pos
        self.transform.size = Size(Target.W, self.vec.length())
        self.color = Target.COLOR
        self.set_parent(Scroll())

    def render(self, sur):
        pygame.draw.line(
            sur,
            self.color,
            self.transform.pos - self.vec / 2,
            self.transform.pos + self.vec / 2,
            Target.THICKNESS,
        )

    def collide_point(self, p: Vector2):
        return point_collide_segment(
            p,
            [self.transform.pos - self.vec / 2, self.transform.pos + self.vec / 2],
            Target.THICKNESS,
        )


class Floor(CollideEntity, metaclass=Singelton):
    THICKNESS = 3
    COLOR = Color("White")
    INITIAL_H = H / 2
    NEW_GEN_DIST_THRESH = 10
    GEN_MIN_DIST = 60
    GEN_MAX_DIST = W // 2
    GEN_MAX_H_OFFSET = 50

    def __init__(self):
        super().__init__()
        self.lines: List[Pos] = [Pos(0, Floor.INITIAL_H), Pos(W, Floor.INITIAL_H)]
        self.transform.pos = self.lines[0].copy()
        self.thickness = Floor.THICKNESS
        self.color = Floor.COLOR

    def get_line_for_x(self, x):
        for i, point in enumerate(self.lines[1:], 1):
            if point.x >= x:
                line = [self.lines[i - 1], point]
                return line

    def generate_new_point(self):
        height_offset = randint(-Floor.GEN_MAX_H_OFFSET, Floor.GEN_MAX_H_OFFSET)
        x_offset = randint(Floor.GEN_MIN_DIST, Floor.GEN_MAX_DIST)
        new_point = self.lines[-1] + Vector2(x_offset, height_offset)
        new_point.y = pygame.math.clamp(new_point.y, 0, H)

        self.lines.append(new_point)

    def update(self, dt):
        super().update(dt)
        assert len(self.lines) > 1, "Floor has to have at least 2 points"
        for l in self.lines:
            l.x -= Player().speed * dt
        if self.lines[-1].x - W <= Floor.NEW_GEN_DIST_THRESH:
            self.generate_new_point()

    def render(self, sur):
        pygame.draw.lines(
            sur,
            self.color,
            False,
            self.lines,
            self.thickness,
        )


class Arrow(CollideEntity):
    LENGTH = 50
    THICKNESS = 1
    COLOR = Color("White")
    POWER_FACTOR = 20
    MAX_POWER = 80

    def __init__(self, player: "Player"):
        super().__init__()
        self.length = 50
        self.player = player
        self.origin = (
            self.player.get_arc_midpoint() - self.player.bow_dir * self.length * 0.75
        )
        self.transform.pos = self.origin + self.player.bow_dir * self.length
        self.is_attached = True
        self.hit = False
        self.launching = False
        self.power = 0
        self.velocity = Vector2()
        InputManager().register_mouse_pressed(BUTTON_LEFT, self, self.on_mouse_pressed)
        InputManager().register_mouse_released(
            BUTTON_LEFT, self, self.on_mouse_released
        )
        self.last_pos: Vector2 = None
        self.set_parent(Scroll())

    @classmethod
    def register_collision_functions(cls):

        return [
            CollisionData(Floor, Arrow.collide_with_floor),
            CollisionData(Target, Arrow.collide_with_target),
        ]

    def collide_with_floor(self, floor: Floor):
        if self.is_attached or self.hit:
            return
        if point_collide_segment(self.transform.pos, floor.lines, Floor.THICKNESS * 2):
            self.hit = True

    def collide_with_target(self, target: Target):
        if self.is_attached or self.hit:
            return
        if target.collide_point(self.transform.pos):
            self.hit = True
            target.color = Target.HIT_COLOR

    def on_mouse_pressed(self):
        if self.is_attached:
            self.launching = True

    def on_mouse_released(self):
        self.is_attached = False
        if self.launching:
            self.player.arrow = GameManager().instatiate(Arrow(self.player))
            self.last_pos = (self.transform.pos - self.origin) / 2 + self.origin
            self.velocity += self.player.bow_dir * self.power
        self.launching = False

    def update(self, dt):
        super().update(dt)
        if self.is_attached:
            self.origin = (
                self.player.get_arc_midpoint()
                - self.player.bow_dir * self.length * 0.75
            )
            self.transform.pos = self.origin + self.player.bow_dir * self.length
        if self.launching:
            self.power += Arrow.POWER_FACTOR * dt
            self.power = min(self.power, Arrow.MAX_POWER)
        if not self.is_attached and not self.hit:
            assert self.last_pos
            my_dir = (self.transform.pos - self.last_pos).normalize()
            self.last_pos = (self.transform.pos - self.origin) / 2 + self.origin
            self.transform.pos += self.velocity
            self.origin = self.transform.pos - my_dir * self.length
            self.velocity *= 1 - 0.1 * dt
            self.velocity.y += G * dt
        if self.hit:
            self.origin.x -= Player().speed * dt

    def render(self, sur):
        pygame.draw.line(
            sur, Arrow.COLOR, self.origin, self.transform.pos, Arrow.THICKNESS
        )


class Player(CollideEntity, metaclass=Singelton):
    SIZE = Size(10, 30)
    X = W / 8
    COLOR = Color("White")
    INITIAL_SPEED = 120
    BOW_OFFSET = 0
    BOW_LENGTH = pi / 3

    def __init__(self):
        super().__init__()
        self.transform.size = Player.SIZE.copy()
        self.transform.pos = Pos(
            Player.X, Floor().INITIAL_H - self.transform.size.h - 50
        )
        self.speed = Player.INITIAL_SPEED
        self.bow_dir = Vector2(0, 1)
        self.arrow = GameManager().instatiate(Arrow(self))
        self.touching_floor = False
        self.vel_y = 0

    @classmethod
    def register_collision_functions(cls):
        return [CollisionData(Floor, Player.collide_with_floor)]

    def collide_with_floor(self, floor: Floor):
        self.touching_floor = False
        if point_collide_segment(
            self.transform.rect().bottomleft, floor.lines, floor.thickness
        ):
            self.touching_floor = True
        if point_collide_segment(
            self.transform.rect().bottomright, floor.lines, floor.thickness
        ):
            self.touching_floor = True

    def get_arc_midpoint(
        self,
    ):
        bow_rect = self.create_bow_rect()
        # 1. Find the center of the bounding rect. This is the center of the circle.

        bow_angle = atan2(-self.bow_dir.y, self.bow_dir.x)

        radius2 = Vector2(bow_rect.size) / 2
        radius2.x *= cos(bow_angle)
        radius2.y = -radius2.y * sin(bow_angle)
        offset_center = bow_rect.center + radius2

        return offset_center

    def create_bow_rect(self):
        bow_rect = Rect(Pos(0, 0), (70, 70))
        bow_rect.center = self.transform.center + self.bow_dir * Player.BOW_OFFSET
        return bow_rect

    def update(self, dt):
        super().update(dt)
        if self.touching_floor:
            self.vel_y = 0
            right = self.transform.rect().right
            line = Floor().get_line_for_x(right)
            if line[0].y >= self.transform.rect().bottom > line[1].y:  # up slope
                self.transform.pos.y = get_y_at(line, right) - self.transform.size.h
        else:
            self.vel_y += G * 5 * dt
            self.transform.pos.y += self.vel_y
        unnormalized = Vector2(pygame.mouse.get_pos()) - Vector2(
            self.transform.rect().center
        )
        if unnormalized.length_squared() == 0:
            self.bow_dir = Vector2(0, 1)
        else:
            self.bow_dir = (
                Vector2(pygame.mouse.get_pos()) - Vector2(self.transform.rect().center)
            ).normalize()

    def render_bow(self, sur: Surface):
        bow_rect = self.create_bow_rect()
        bow_angle = atan2(-self.bow_dir.y, self.bow_dir.x)
        pygame.draw.arc(
            sur,
            Player.COLOR,
            bow_rect,
            bow_angle - Player.BOW_LENGTH / 2,
            bow_angle + Player.BOW_LENGTH / 2,
        )

    def render(self, sur):
        pygame.draw.rect(sur, Player.COLOR, self.transform.rect())
        self.render_bow(sur)

    def render_debug(self, sur):
        pygame.draw.line(
            sur,
            Color("Red"),
            self.transform.rect().center,
            self.transform.rect().center + Player.BOW_OFFSET * self.bow_dir,
        )
        pygame.draw.rect(sur, Color("Red"), self.create_bow_rect(), 1)
        arc_midpoint = self.get_arc_midpoint()
        pygame.draw.circle(sur, Color("Red"), arc_midpoint, 3)
        x = pygame.mouse.get_pos()[0]
        pygame.draw.circle(
            sur,
            Color("Red"),
            (
                x,
                get_y_at(
                    Floor().get_line_for_x(x),
                    x,
                ),
            ),
            3,
        )


def start_game_scene():
    GameManager().instatiate(Floor())
    GameManager().instatiate(Target(Pos(300, 100), 0))
    GameManager().instatiate(Target(Pos(400, 100), 90))
    GameManager().instatiate(Target(Pos(500, 100), 60))
    GameManager().instatiate(Player())


def main():
    start_game_scene()

    pygame.init()
    pygame.display.set_caption("Archer")
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
