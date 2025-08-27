from pygame import Surface, Color
import pygame
from pygame.math import clamp
from pyengine import *

from math import pi, tan, floor, ceil

W = 1280
H = 720
BG = Color(40, 40, 40)


# The actual map:
# fmt: off
CELLS = [
#    0 1 2 3 4 5               6               7 8 9 0             1                2              3 4 5 6 7 8
    [0,0,0,0,0,0,              0,              0,0,0,0,            0,               0,             0,0,0,0,0,0],# 0
    [0,0,0,0,0,Color("Orange"),Color("Grey"),  0,0,0,Color("Blue"),Color("Magenta"),1,Color("Red"),1,0,0,0,0,0],# 1
    [0,0,0,0,0,0,              Color("Yellow"),0,0,0,0,            0,               0,             0,0,0,0,0,0],# 2
    [0,0,0,0,0,0,              Color("Pink"),  0,0,0,0,            1,               0,             0,0,0,0,0,0],# 3
    [0,0,0,0,0,Color("Black"), 0,              0,0,0,0,            Color("Green"),  0,             0,0,0,0,0,0],# 4
    [0,0,0,0,0,Color("Orange"),Color("Grey"),  0,0,0,Color("Blue"),Color("Magenta"),1,Color("Red"),1,0,0,0,0,0],# 5
    [0,0,0,0,0,0,              Color("Yellow"),0,0,0,0,            0,               0,             0,0,0,0,0,0],# 6
    [0,0,0,0,0,0,              0,              0,0,0,0,            0,               0,             0,0,0,1,0,0],# 7
]
# fmt: on
CELL_SIZE = Size(W / len(CELLS[0]), H / len(CELLS))


class Player(Entity):
    def __init__(self, center: Pos):
        super().__init__()
        self.transform.center = center
        self.look_distance = 100
        self.fov = pi * 0.4
        self.dir = Vector2(0, -1)
        self.dir_velocity = 0
        self.forward_velocity = 0
        self.forward_speed = 100
        self.rotation_speed = 1.5
        self.color = Color("Magenta")

        self.half_range_length = self.look_distance * tan(self.fov * 0.5)

    def start(self):
        InputManager().register_key_down(
            pygame.K_LEFT, self, lambda: self.set_dir_velocity(-self.rotation_speed)
        ).register_key_down(
            pygame.K_RIGHT, self, lambda: self.set_dir_velocity(self.rotation_speed)
        ).register_key_down(
            pygame.K_UP, self, lambda: self.set_forward_velocity(self.forward_speed)
        ).register_key_down(
            pygame.K_DOWN, self, lambda: self.set_forward_velocity(-self.forward_speed)
        ).register_key_up(
            pygame.K_LEFT, self, lambda: self.set_dir_velocity(0)
        ).register_key_up(
            pygame.K_RIGHT, self, lambda: self.set_dir_velocity(0)
        ).register_key_up(
            pygame.K_UP, self, lambda: self.set_forward_velocity(0)
        ).register_key_up(
            pygame.K_DOWN, self, lambda: self.set_forward_velocity(0)
        )
        return super().start()

    def set_dir_velocity(self, dir_vel):
        self.dir_velocity = dir_vel

    def set_forward_velocity(self, forward_velocity):
        self.forward_velocity = forward_velocity

    def update(self, dt):
        self.dir.rotate_rad_ip(self.dir_velocity * pi * dt)
        self.transform.center += self.dir * self.forward_velocity * dt


class Ray(Entity):
    def __init__(self, origin: Pos, dir: Pos):
        super().__init__()
        self.transform.center = origin
        self.dir = dir
        self.color = Color("Purple")
        self.head = self.transform.center + self.dir
        self.updating = False

    def magnitude(self):
        return (self.head - self.transform.center).magnitude()

    def snap(x, dx):
        if dx < 0:
            return floor(x)
        else:
            return ceil(x)

    def in_scene(self, p):

        return 0 < p.x and 0 < p.y and p.x < W and p.y < H

    def get_cur_cell(self):
        e_head = self.head.copy()
        if self.in_scene(e_head + self.dir):
            e_head += self.dir
        y = floor(e_head.y / CELL_SIZE.h)
        x = floor(e_head.x / CELL_SIZE.w)
        return (clamp(y, 0, len(CELLS) - 1), clamp(x, 0, len(CELLS[0]) - 1))

    def step(self):

        cand1 = self.head + self.dir
        grid_coord = Pos(cand1.x / CELL_SIZE.w, cand1.y / CELL_SIZE.h)
        d = cand1 - self.transform.center
        if d.x != 0:
            k = d.y / d.x
            c = self.transform.center.y - k * self.transform.center.x
            x_snap = Ray.snap(grid_coord.x, d.x) * CELL_SIZE.w
            y_snap = x_snap * k + c
            cand1 = Pos(x_snap, y_snap)

            if k != 0:
                y_snap = Ray.snap(grid_coord.y, d.y) * CELL_SIZE.h
                x_snap = (y_snap - c) / k
                cand2 = Pos(x_snap, y_snap)

                if (cand1 - self.head).magnitude() > (cand2 - self.head).magnitude():
                    cand1 = cand2
        else:
            cand1.y = Ray.snap(grid_coord.y, d.y) * CELL_SIZE.h
        return cand1

    def update(self, dt):
        self.updating = True
        self.head = self.transform.center
        cur_cell = self.get_cur_cell()
        while self.in_scene(self.head) and CELLS[cur_cell[0]][cur_cell[1]] == 0:
            self.head = self.step()
            cur_cell = self.get_cur_cell()
        self.updating = False


class Minimap(Entity):
    def __init__(self, pos: Pos, size: Size, player: Player, rays: list[Ray] = []):
        super().__init__()
        self.z_index = 100
        self.transform.pos = pos
        self.transform.size = size
        self.player = player
        self.row_count = len(CELLS)
        self.col_count = len(CELLS[0])

        self.grid_color = Color(90, 90, 90)
        self.player_radius_render = self.transform.size.magnitude() / 100
        self.rays = rays

    def cell_size(self) -> Size:
        return Size(
            self.transform.size.w / self.col_count,
            self.transform.size.h / self.row_count,
        )

    def world_cell_size(self):
        cell_size = self.cell_size()
        return Size(
            cell_size.w * W / self.transform.size.w,
            cell_size.h * H / self.transform.size.h,
        )

    def screen_coords_to_minimap(self, coords: Vector2):
        return (
            Vector2(
                coords.x * self.transform.size.w / W,
                coords.y * self.transform.size.h / H,
            )
            + self.transform.pos
        )

    def minimap_coord_to_screen(self, coords: Vector2):
        return (
            Vector2(
                coords.x * W / self.transform.size.w,
                coords.y * H / self.transform.size.h,
            )
            - self.transform.pos
        )

    def render_mini_player(self, sur: Surface):
        player_mini_pos = self.screen_coords_to_minimap(self.player.transform.center)

        pygame.draw.circle(
            sur,
            self.player.color,
            player_mini_pos,
            self.player_radius_render,
        )

        # draw fov
        size_factor = self.transform.size.magnitude() / Vector2(W, H).magnitude()
        r1_length = self.player.half_range_length * size_factor
        half_fov_v = self.player.dir.rotate_rad(pi * 0.5) * r1_length
        mini_look_distance = self.player.look_distance * size_factor
        r1 = player_mini_pos + self.player.dir * mini_look_distance + half_fov_v
        r2 = player_mini_pos + self.player.dir * mini_look_distance - half_fov_v

        sub_sur_pos = player_mini_pos - Pos(1) * mini_look_distance * 2
        sub_sur_size = Size(1) * mini_look_distance * 4
        fov_sub_sur = Surface(sub_sur_size, pygame.SRCALPHA)
        fov_sub_sur.set_alpha(127)
        pygame.draw.polygon(
            fov_sub_sur,
            self.player.color,
            [
                player_mini_pos - sub_sur_pos,
                r1 - sub_sur_pos,
                r2 - sub_sur_pos,
            ],
        )
        sur.blit(fov_sub_sur, sub_sur_pos)

    def render_mini_rays(self, sur: Surface):
        for ray in self.rays:
            if ray.updating:
                continue
            ray_mini_origin = self.screen_coords_to_minimap(ray.transform.center)
            ray_mini_head_pos = self.screen_coords_to_minimap(ray.head)
            pygame.draw.line(sur, ray.color, ray_mini_origin, ray_mini_head_pos)

    def render(self, sur: Surface):
        # draw grid
        cell_size = self.cell_size()
        for x in range(self.col_count + 1):
            pygame.draw.line(
                sur,
                self.grid_color,
                self.transform.pos + Pos(x * cell_size.x, 0),
                self.transform.pos + Pos(x * cell_size.x, self.transform.size.h),
                width=3,
            )
        for y in range(self.row_count + 1):
            pygame.draw.line(
                sur,
                self.grid_color,
                self.transform.pos + Pos(0, y * cell_size.y),
                self.transform.pos + Pos(self.transform.size.w, y * cell_size.y),
                width=3,
            )

        # draw cells
        for y, row in enumerate(CELLS):
            for x, color in enumerate(row):
                if color != 0:
                    pygame.draw.rect(
                        sur,
                        self.grid_color,
                        pygame.Rect(
                            Pos(x * cell_size.w, y * cell_size.h) + self.transform.pos,
                            cell_size,
                        ),
                    )
        # draw player dot
        self.render_mini_player(sur)
        self.render_mini_rays(sur)


class World(Entity):
    def __init__(self, pos: Pos, size: Size, samples, player: Player):
        super().__init__()
        self.transform.pos = pos
        self.transform.size = size
        self.player = player
        self.samples = samples
        self.rays: list[Ray] = []
        ray_dir = player.dir.rotate_rad(-player.fov / 2)
        self.strip_width = ceil(self.transform.size.w / samples)
        for _ in range(samples):
            ray = Ray(self.player.transform.center, ray_dir.copy())
            self.rays.append(ray)
            Vector2.rotate_rad_ip(ray_dir, player.fov / samples)

    def start(self):
        GameManager().instatiate(*self.rays)
        return super().start()

    def update(self, dt):
        ray_dir = self.player.dir.rotate_rad(-self.player.fov / 2)
        for ray in self.rays:
            ray.dir = ray_dir.copy()
            ray_dir.rotate_ip_rad(self.player.fov / self.samples)
            ray.transform.center = self.player.transform.center

    def render(self, sur: Surface):
        for i in range(self.samples):
            ray = self.rays[i]
            if ray.updating:
                continue
            cur_cell = ray.get_cur_cell()
            color = Color("White")
            distance = ray.magnitude()
            if (
                CELLS[cur_cell[0]][cur_cell[1]] != 0
                and distance > 0
                and ray.in_scene(ray.head)
            ):
                if type(CELLS[cur_cell[0]][cur_cell[1]]) == Color:
                    color = CELLS[cur_cell[0]][cur_cell[1]]
                else:
                    color = Color("White")

                h = (
                    self.transform.size.h
                    * (CELL_SIZE.w / self.transform.size.w * W)
                    / distance
                )
                color = color.lerp(
                    Color("Black"), clamp(distance / self.transform.size.w, 0, 1)
                )
                pygame.draw.rect(
                    sur,
                    color,
                    pygame.Rect(
                        self.transform.size.w / self.samples * i,
                        (self.transform.size.h - h) / 2,
                        self.strip_width,
                        h,
                    ),
                )


def main():

    player = Player(Pos(500, 500))
    world = World(Pos(0, 0), Size(1000, 700), 200, player)
    minimap = Minimap(Pos(10, 10), world.transform.size * 0.25, player)
    GameManager().instatiate(minimap, player, world)

    GameManager().fps = 100

    screen = pygame.display.set_mode((W, H))

    UpdateManager().start_fixed_update_loop()
    GameManager().debug = True
    while not GameManager().should_exit:
        screen.fill(BG)
        GameManager().update()
        GameManager().render(screen)
        pygame.display.flip()
    UpdateManager().stop_fixed_update_loop()


if __name__ == "__main__":
    main()
