import pygame
from pygame import BUTTON_LEFT, K_SPACE, Color, K_r, Rect
from pyengine import *

W = 1280
H = 720
pan_center = Pos(W / 2, H / 2)
BG = Color("Black")
G = 0.1
scale = 1.0
MAX_MASS = 100000000

# CENTER + (pos-CENTER)*scale = res
# pos = res-CENTER/scale + CENTER


def world_to_screen(pos: Pos):
    return pan_center + (pos - Pos(W / 2, H / 2)) * scale


def screen_to_world(pos: Pos):
    return (pos - pan_center) / scale + Pos(W / 2, H / 2)


class Slider(Entity):
    HEIGHT = 10
    COLOR = Color("White")
    CONTROL_WIDTH = 5

    def __init__(
        self, width, initial_value, on_change, min=0, max=1, color=COLOR, name=""
    ):
        super().__init__()
        self.transform.size = Size(width, Slider.HEIGHT)
        self.value = initial_value
        self.on_change = on_change
        self.color = color
        self.min = min
        self.max = max
        assert self.min <= self.value <= self.max
        InputManager().register_mouse_pressed(pygame.BUTTON_LEFT, self, self.on_pressed)
        InputManager().register_mouse_released(
            pygame.BUTTON_LEFT, self, self.on_release
        )
        self.dragging = False
        self.name_sur = GameManager().font.render(name, True, Slider.COLOR)

    def set_value(self, value):
        self.value = value

    def on_pressed(self):
        mouse_pos = pygame.mouse.get_pos()
        if self.transform.rect().collidepoint(mouse_pos):
            self.dragging = True

    def on_release(self):
        self.dragging = False

    def get_control_rect_center(self):
        offset_val = self.value - self.min
        offset_max = self.max - self.min
        return self.transform.pos.x + self.transform.size.w * offset_val / offset_max

    def get_value_from_x(self, x):
        offset_x = x - self.transform.pos.x
        precentage = offset_x / self.transform.size.w
        return precentage * (self.max - self.min) + self.min

    def update(self, dt):
        super().update(dt)
        if self.dragging:
            mouse_pos = pygame.mouse.get_pos()
            self.value = pygame.math.clamp(
                self.get_value_from_x(mouse_pos[0]), self.min, self.max
            )
            self.on_change(self.value)

    def render(self, sur):
        super().render(sur)
        sur.blit(self.name_sur, self.transform.pos - Pos(0, self.name_sur.get_height()))
        pygame.draw.rect(
            sur,
            Slider.COLOR,
            Rect(
                self.transform.pos.x,
                self.transform.pos.y + self.transform.size.h / 3,
                self.transform.size.w,
                self.transform.size.h / 3,
            ),
        )
        pygame.draw.rect(
            sur,
            self.color,
            Rect(
                self.get_control_rect_center() - Slider.CONTROL_WIDTH / 2,
                self.transform.pos.y,
                Slider.CONTROL_WIDTH,
                Slider.HEIGHT,
            ),
        )
        font_sur = GameManager().font.render(f"{self.value:.2f}", False, Slider.COLOR)
        sur.blit(
            font_sur,
            (
                self.get_control_rect_center() - font_sur.get_width() / 2,
                self.transform.rect().bottom,
            ),
        )


class Planet(Entity):
    def __init__(
        self,
        initial_pos: Pos,
        initial_velocity: Vector2,
        mass: float,
        radius: float,
        color: pygame.Color,
        on_drag=None,
    ):
        super().__init__()
        self.transform.pos = initial_pos
        self.initial_velocity = initial_velocity
        self.velocity = self.initial_velocity.copy()
        self.mass = mass
        self.radius = radius
        self.color = color
        self.dragging = False
        InputManager().register_mouse_pressed(BUTTON_LEFT, self, self.on_press)
        InputManager().register_mouse_released(BUTTON_LEFT, self, self.on_release)
        self.on_drag = on_drag

    def on_press(self):
        if (
            world_to_screen(self.transform.pos).distance_to(pygame.mouse.get_pos())
            < self.radius * scale
        ):
            self.dragging = True

    def on_release(self):
        self.dragging = False

    def update(self, dt):
        super().update(dt)
        if self.dragging:
            self.transform.pos = screen_to_world(Pos(pygame.mouse.get_pos()))
            if self.on_drag:
                self.on_drag()

    def update_velocity(self, all_planets: List["Planet"], dt):
        for planet in all_planets:
            if planet.transform.pos == self.transform.pos:
                continue
            sqr_dist = (planet.transform.pos - self.transform.pos).magnitude_squared()
            force_dir = (planet.transform.pos - self.transform.pos).normalize()
            force = force_dir * G * self.mass * planet.mass / sqr_dist
            acceleration = force / self.mass
            self.velocity += acceleration * dt

    def update_position(self, dt):
        self.transform.pos += self.velocity * dt

    def set_mass(self, mass):
        self.mass = mass

    def set_velocity(self, velocity: Vector2):
        self.initial_velocity = velocity
        self.velocity = self.initial_velocity.copy()

    def render(self, sur):
        pygame.draw.circle(
            sur,
            self.color,
            world_to_screen(self.transform.pos),
            self.radius * scale,
        )

    def copy(self):
        return Planet(
            self.transform.pos.copy(),
            self.velocity.copy(),
            self.mass,
            self.radius,
            self.color,
        )


class SollarSystem(Entity):
    SLIDERS_X = 30
    SLIDERS_PADDING_Y = 30
    SLIDERS_WIDTH = W / 3
    ORBIT_SIMULATION_STEPS = 10000

    def __init__(self, planets: List[Planet]):
        super().__init__()
        self.orbits = [[planet.transform.pos.copy()] for planet in planets]
        self.simulating = False
        self.running = False
        self.planets = planets
        for planet in self.planets:
            planet.on_drag = self.calculate_orbits
        self.orbits_sur = None
        self.sliders = self.create_sliders()
        self.calculate_orbits()
        self.z_index = -1
        self.dragging = False
        self.dragging_start_pos = None
        InputManager().register_key_up(K_SPACE, self, self.on_space)
        InputManager().register_mouse_scroll(self, self.on_scroll)
        InputManager().register_mouse_pressed(BUTTON_LEFT, self, self.on_drag)
        InputManager().register_mouse_released(BUTTON_LEFT, self, self.on_release_drag)

    def on_drag(self):
        if any(planet.dragging for planet in self.planets) or any(
            slider.dragging for slider in self.sliders
        ):
            return
        self.dragging = True
        self.dragging_start_pos = Pos(pygame.mouse.get_pos())

    def on_release_drag(self):
        self.dragging = False

    def kill(self):
        super().kill()
        UpdateManager().stop_fixed_update_loop()
        GameManager().destroy(*self.planets, *self.sliders)

    def on_scroll(self, _scroll):
        global scale
        scale = max(scale + _scroll.y * 0.1, 0.1)

    def on_space(self):
        self.running = not self.running
        if self.running:
            UpdateManager().start_fixed_update_loop()
        else:
            UpdateManager().stop_fixed_update_loop()

    def calculate_orbits(self):
        self.orbits = [[planet.transform.pos.copy()] for planet in self.planets]
        temp = self.planets
        self.planets = [planet.copy() for planet in self.planets]
        self.simulate(SollarSystem.ORBIT_SIMULATION_STEPS)
        self.planets = temp
        self.orbits_sur = None

    def create_sliders(self):
        def set_planet_mass(planet: Planet, mass):
            planet.set_mass(mass)
            self.calculate_orbits()

        def set_planet_vel_x(planet: Planet, x):
            planet.set_velocity(Vector2(x, planet.velocity.y))
            self.calculate_orbits()

        def set_planet_vel_y(planet: Planet, y):
            planet.set_velocity(Vector2(planet.velocity.x, y))
            self.calculate_orbits()

        sliders: List[Slider] = []
        last_y = SollarSystem.SLIDERS_PADDING_Y
        for planet in self.planets:
            sliders.append(
                GameManager().instatiate(
                    Slider(
                        SollarSystem.SLIDERS_WIDTH / 2,
                        planet.mass,
                        lambda mass, planet=planet: set_planet_mass(planet, mass),
                        0.1,
                        MAX_MASS,
                        planet.color,
                        "Mass",
                    )
                )
            )
            sliders[-1].transform.pos = Pos(SollarSystem.SLIDERS_X, last_y)
            sliders.append(
                GameManager().instatiate(
                    Slider(
                        SollarSystem.SLIDERS_WIDTH,
                        planet.velocity.x,
                        lambda x, planet=planet: set_planet_vel_x(planet, x),
                        -100,
                        100,
                        planet.color,
                        "Velocity x",
                    )
                )
            )
            sliders[-1].transform.pos = Pos(
                SollarSystem.SLIDERS_X + SollarSystem.SLIDERS_WIDTH / 2 + 20, last_y
            )
            sliders.append(
                GameManager().instatiate(
                    Slider(
                        SollarSystem.SLIDERS_WIDTH,
                        planet.velocity.y,
                        lambda y, planet=planet: set_planet_vel_y(planet, y),
                        -100,
                        100,
                        planet.color,
                        "Velocity y",
                    )
                )
            )
            sliders[-1].transform.pos = Pos(
                SollarSystem.SLIDERS_X + SollarSystem.SLIDERS_WIDTH * 1.5 + 40, last_y
            )

            last_y += sliders[-1].transform.size.h + SollarSystem.SLIDERS_PADDING_Y
        return sliders

    def simulate(self, steps):
        self.simulating = True
        for _ in range(steps):
            self.fixed_update(UpdateManager.FIXED_DT)
            for i, planet in enumerate(self.planets):
                self.orbits[i].append(planet.transform.pos.copy())
        self.simulating = False

    def update(self, dt):
        global pan_center
        for i, planet in enumerate(self.planets):
            self.sliders[i * 3 + 1].set_value(planet.velocity.x)
            self.sliders[i * 3 + 2].set_value(planet.velocity.y)
        if self.dragging:
            mouse_pos = Pos(pygame.mouse.get_pos())  # screen-space
            delta = mouse_pos - self.dragging_start_pos
            pan_center += delta
            self.dragging_start_pos = (
                mouse_pos  # Update to last mouse pos, not pan center
            )

    def fixed_update(self, fixed_dt):
        super().fixed_update(fixed_dt)
        if self.running or self.simulating:
            for i, planet in enumerate(self.planets):
                planet.update_velocity(self.planets, fixed_dt)

            for planet in self.planets:
                planet.update_position(fixed_dt)

    def get_orbits_sur(self, size: Size):
        sur = Surface(size)
        for orbit, planet in zip(self.orbits, self.planets):
            if len(orbit) == 0:
                continue
            starting_point = orbit[0]
            for pos in orbit[1:]:
                pygame.draw.line(
                    sur,
                    planet.color,
                    world_to_screen(starting_point),
                    world_to_screen(pos),
                    2,
                )
                starting_point = pos
        return sur

    def render(self, sur):
        super().render(sur)
        self.orbits_sur = self.get_orbits_sur(sur.get_size())

        sur.blit(self.orbits_sur, Pos(0, 0))


class SollarSystemManager(Entity):
    KEY_MAP_COLOR = Color("Purple")

    def __init__(self):
        super().__init__()
        self.sollar_system = None
        InputManager().register_key_up(K_r, self, self.create_sollar_system)
        self.key_map_sur = self.create_key_map()

    def create_key_map(self):
        start_animation = GameManager().font.render(
            "Space:              start animation",
            True,
            SollarSystemManager.KEY_MAP_COLOR,
        )
        reset = GameManager().font.render(
            "R:                     reset start position",
            True,
            SollarSystemManager.KEY_MAP_COLOR,
        )
        drag = GameManager().font.render(
            "Drag planet:     to set position", True, SollarSystemManager.KEY_MAP_COLOR
        )
        sur = Surface(
            Size(
                reset.get_width(),
                start_animation.get_height() + reset.get_height() + drag.get_height(),
            )
        )
        sur.blits(
            [
                (start_animation, (0, 0)),
                (reset, (0, start_animation.get_height())),
                (drag, (0, start_animation.get_height() + reset.get_height())),
            ]
        )
        return sur

    def start(self):
        super().start()
        self.create_sollar_system()

    def create_sollar_system(self):
        global pan_center
        pan_center.x = W / 2
        pan_center.y = H / 2
        if self.sollar_system:
            GameManager().destroy(self.sollar_system)
        sun = GameManager().instatiate(
            Planet(pan_center.copy(), Vector2(0, 0), MAX_MASS, 220, Color("Yellow"))
        )

        earth = GameManager().instatiate(
            Planet(
                sun.transform.pos + Pos(1000, 0),
                Vector2(0, 30),
                40000,
                20,
                Color("Blue"),
            )
        )
        moon = GameManager().instatiate(
            Planet(
                earth.transform.pos + Pos(10, 0), Vector2(0, 50), 1000, 7, Color("Grey")
            )
        )
        self.sollar_system = GameManager().instatiate(SollarSystem([sun, earth, moon]))

    def render(self, sur):
        sur.blit(self.key_map_sur, Pos(30, H - self.key_map_sur.get_height()))


def main():

    pygame.init()
    pygame.display.set_caption("pe")
    screen = pygame.display.set_mode((W, H))

    UpdateManager().FIXED_DT = 0.1
    GameManager().instatiate(SollarSystemManager())

    while not GameManager().should_exit:
        screen.fill(BG)
        GameManager().update()
        GameManager().render(screen)
        pygame.display.flip()

    UpdateManager().stop_fixed_update_loop()


if __name__ == "__main__":
    main()
    pygame.quit()
