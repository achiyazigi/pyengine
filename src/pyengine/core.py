from dataclasses import dataclass
from enum import Enum
from math import pi, sin
import multiprocessing
import multiprocessing.queues
from threading import Timer
import time
import pygame
from pygame import Color, Rect, Vector2, Surface
from abc import ABC, ABCMeta
from typing import (
    Callable,
    Dict,
    List,
    MutableSequence,
    Sequence,
    Set,
    Tuple,
    Union,
    overload,
    TypeVar
)
import bisect


class Singelton(ABCMeta):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singelton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


Pos = Vector2


def Vector2Left():
    return Vector2(-1, 0)


def Vector2Right():
    return Vector2(1, 0)


def Vector2Up():
    return Vector2(0, -1)


def Vector2Down():
    return Vector2(0, 1)


class Size(Vector2):

    @overload
    def __init__(self, w: float, h: float) -> None: ...

    @overload
    def __init__(self, w_h: Tuple[float, float] | float) -> None: ...

    @overload
    def __init__(self) -> None: ...

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @property
    def w(self):
        return self.x

    @w.setter
    def w(self, w):
        self.x = w

    @property
    def h(self):
        return self.y

    @h.setter
    def h(self, h):
        self.y = h


# def clip(tl: Vector2, vec: Vector2, br: Vector2):
#     vec.x = min(max(tl.x, vec.x), br.x)
#     vec.y = min(max(tl.y, vec.y), br.y)
#     return vec


class Transform:
    def __init__(self):
        self.pos = Pos()
        self.size = Size(0, 0)

    def rect(self):
        return Rect(self.pos, self.size)

    @property
    def center(self):
        return self.pos + self.size / 2

    @center.setter
    def center(self, center: Pos):
        self.pos = center - self.size / 2


class EntityState(Enum):
    Initialized = (0,)
    Started = (1,)
    Destroyed = 2


class Entity(ABC):
    """
    Every class participating in the game loop
    should inherite from this class.

    The methods update() and then later render()
    will be called before every display.flip().
    The properties of this class should not be
    changed between update() and render().

    The z_index determine the render order
    and can be set at any point.
    Lower z_index meaning farther from camera.

    update_order: lower value get updated first
    and can be set at any point.

    Entity should be managed by Scene which should
    be managed by GameManager. Thus, don't ever call
    kill() nor start() directly. Use GameManager().instatiate()
    and GameManager().destroy() in your start() implementation
    instead.
    """

    def __init__(self):
        self.transform = Transform()
        self._z_index = 0
        self._update_order = 0
        self.should_render = True
        self.state = EntityState.Initialized
        self.offset_parent = Pos(0, 0)
        self.parent: Entity = None

    def start(self):
        """
        Will be called when entity start to be managed by GameManager()
        """
        RenderManager().register(self)
        UpdateManager().register(self)
        self.state = EntityState.Started

    def update(self, dt):
        """
        Will be called before every frame
        """
        if self.parent:
            self.transform.pos += self.parent.transform.pos - self.offset_parent
            self.offset_parent = self.parent.transform.pos.copy()

    def fixed_update(self, fixed_dt):
        """
        Will be called at a fixed
        (and usually faster than update()) rate
        """
        pass

    def render(self, sur: Surface):
        """
        Should be the only interaction with the screen's surface
        """
        pass

    def render_debug(self, sur: Surface):
        axis_length = 20
        pygame.draw.line(
            sur,
            Color("Grey"),
            self.transform.pos + Vector2Left() * axis_length / 2,
            self.transform.pos + Vector2Right() * axis_length / 2,
        )
        pygame.draw.line(
            sur,
            Color("Grey"),
            self.transform.pos + Vector2Up() * axis_length / 2,
            self.transform.pos + Vector2Down() * axis_length / 2,
        )
        type_name_sur = GameManager().font.render(
            type(self).__name__, False, Color("Grey")
        )
        sur.blit(type_name_sur, self.transform.pos)

    def kill(self):
        """
        Will be called on destroy (usually when changing scene).
        Don't call directly, use GameManager().destroy()
        """
        UpdateManager().unregister(self)
        RenderManager().unregister(self)
        self.state = EntityState.Destroyed

    def set_parent(self, parent):
        self.parent = parent
        self.offset_parent = self.parent.transform.pos.copy()

    @property
    def z_index(self):
        return self._z_index

    @z_index.setter
    def z_index(self, z_index):
        if self.state == EntityState.Started:
            RenderManager().unregister(self)
            self._z_index = z_index
            RenderManager().register(self)
            InputManager().update_callbacks_order()
        else:
            self._z_index = z_index

    @property
    def update_order(self):
        return self._update_order

    @update_order.setter
    def update_order(self, update_order):
        if self.state == EntityState.Started:
            UpdateManager().unregister(self)
            self._update_order = update_order
            UpdateManager().register(self)
        else:
            self._update_order = update_order


CollisionFunction = Callable[[Entity, Entity], None]


# TODO:
# get rid of this discusting useless dataclass
@dataclass
class CollisionData:
    type_other: type  # the mro for this type must contain CollideEntity
    collision_function: CollisionFunction


class CollideEntity(Entity):
    """
    This class automatically register the object
    to a collision detection system.
    To register collision functions, return a
    list of CollisionData by overriding the
    method register_collision_functions().
    """

    # Yuk!
    @classmethod
    def register_collision_functions(cls) -> list[CollisionData]:
        return []

    def __init__(self):
        super().__init__()

    def start(self):
        super().start()
        ColliderManager().register(self)
        for collision_data in self.register_collision_functions():
            ColliderManager().describe_collision(
                type(self), collision_data.type_other, collision_data.collision_function
            )

        for base_type in type(self).mro()[1:]:
            if base_type == CollideEntity:
                break
            collide_with_set = ColliderManager().graph.edges.get(base_type, {})
            for collide_with in collide_with_set:
                func = ColliderManager().collision_functions_dict[
                    (base_type, collide_with)
                ]
                ColliderManager.describe_collision(type(self), collide_with, func)

    def kill(self):
        super().kill()
        ColliderManager().unregister(self)


class Utils:
    

    T = TypeVar('T')
    K = TypeVar('K')

    def remove_from_sorted_list(
        sorted_list: MutableSequence[T], item: T, *, key: Callable[[T], K] = None
    ):
        left = bisect.bisect_left(sorted_list, key(item) if key else item, key=key)
        right = bisect.bisect_right(sorted_list, key(item) if key else item, key=key)
        for i in range(left, right):
            if sorted_list[i] is item:
                sorted_list.pop(i)
                return True
        return False


class UpdateManager(metaclass=Singelton):
    FIXED_DT = 0.01

    def __init__(self):
        self.entityes_sorted: list[Entity] = []
        self.fixed_update_running = True
        self.fixed_update_timer = None
        self.debug_info: Dict[Entity, float] = {}

    def register(self, entity: Entity):
        bisect.insort_right(
            self.entityes_sorted, entity, key=lambda item: item.update_order
        )

    def unregister(self, entity: Entity):
        Utils.remove_from_sorted_list(
            self.entityes_sorted, entity, key=lambda item: item.update_order
        )

    def update(self, dt):
        if GameManager().debug:
            self.update_debug(dt)
        else:
            for entity in self.entityes_sorted:
                entity.update(dt)

    def update_debug(self, dt):
        self.debug_info.clear()
        for entity in self.entityes_sorted:
            start_time = time.time_ns()
            entity.update(dt)
            finish_time = time.time_ns()
            self.debug_info[entity] = finish_time - start_time

    def start_fixed_update_loop(self):
        self.fixed_update_timer = Timer(
            UpdateManager.FIXED_DT, self.start_fixed_update_loop
        )
        self.fixed_update_timer.start()
        self.fixed_update()

    def stop_fixed_update_loop(self):
        if self.fixed_update_timer:
            self.fixed_update_timer.cancel()

    def fixed_update(self):
        ColliderManager().update()
        if GameManager().debug:
            self.fixed_update_debug()
        else:
            for entity in self.entityes_sorted:
                entity.fixed_update(UpdateManager.FIXED_DT)

    def fixed_update_debug(self):
        for entity in self.entityes_sorted:
            start_time = time.time_ns()
            entity.fixed_update(UpdateManager.FIXED_DT)
            finish_time = time.time_ns()
            fixed_update_time = finish_time - start_time
            if entity not in self.debug_info:
                self.debug_info[entity] = 0
            self.debug_info[entity] += fixed_update_time


class RenderManager(metaclass=Singelton):
    def __init__(self):
        self.entityes_sorted: List[Entity] = []
        self.debug_info: Dict[Entity, float] = {}

    def register(self, entity: Entity):
        bisect.insort_right(self.entityes_sorted, entity, key=lambda item: item.z_index)

    def unregister(self, entity: Entity):
        Utils.remove_from_sorted_list(
            self.entityes_sorted, entity, key=lambda item: item.z_index
        )

    def render(self, sur: Surface):
        if GameManager().debug:
            self.render_debug(sur)
        else:
            for entity in self.entityes_sorted:
                if entity.should_render:
                    entity.render(sur)

    def render_debug(self, sur: Surface):
        self.debug_info.clear()
        for entity in self.entityes_sorted:
            start_time = time.time_ns()
            entity.render(sur)
            finish_time = time.time_ns()
            self.debug_info[entity] = finish_time - start_time


# the callback should return true to stop propegate
CallbacksDict = dict[int, list[tuple[Entity, Callable[[], bool]]]]


class InputManager(metaclass=Singelton):
    def __init__(self):
        super().__init__()
        self.callbacks_key_down: CallbacksDict = {}
        self.callbacks_key_up: CallbacksDict = {}
        self.callbacks_mouse_pressed: CallbacksDict = {}
        self.callbacks_mouse_released: CallbacksDict = {}
        self.callbacks_mouse_scroll: List[Tuple[Entity, Callable[[Vector2], None]]] = []
        self.update_callbacks_entities_order = False

    def _update_callbacks_for(self, callbacks: CallbacksDict):
        for val in callbacks.values():
            val.sort(key=lambda e: e[0].z_index, reverse=True)
        self.update_callbacks_entities_order = False

    def update_callbacks_order(self):
        self._update_callbacks_for(self.callbacks_key_down)
        self._update_callbacks_for(self.callbacks_key_up)
        self._update_callbacks_for(self.callbacks_mouse_pressed)
        self._update_callbacks_for(self.callbacks_mouse_released)

    def _register_key(self, callbacks: CallbacksDict, key, entity: Entity, func):
        if key not in callbacks:
            callbacks[key] = []
        callbacks[key].append((entity, func))
        self.update_callbacks_entities_order = True
        # idx = bisect.bisect([e.z_index for e, _ in callbacks[key]], entity.z_index)
        # callbacks[key].insert(idx, (entity, func))

    def register_key_down(self, key, entity: Entity, func):
        self._register_key(self.callbacks_key_down, key, entity, func)
        return self

    def register_key_up(self, key, entity, func):
        self._register_key(self.callbacks_key_up, key, entity, func)
        return self

    def register_mouse_pressed(self, button, entity, func):
        self._register_key(self.callbacks_mouse_pressed, button, entity, func)
        return self

    def register_mouse_released(self, button, entity, func):
        self._register_key(self.callbacks_mouse_released, button, entity, func)

    def register_mouse_scroll(self, entity, func):
        self.callbacks_mouse_scroll.append((entity, func))

    def _trigger_key(callbacks: CallbacksDict, key):
        for entity, func in callbacks.get(key, []):
            if entity in GameManager().entities:
                if func():
                    break

    def trigger_key_down(self, key):
        InputManager._trigger_key(self.callbacks_key_down, key)

    def trigger_key_up(self, key):
        InputManager._trigger_key(self.callbacks_key_up, key)

    def trigger_mouse_pressed(self, button):
        InputManager._trigger_key(self.callbacks_mouse_pressed, button)

    def trigger_mouse_released(self, button):
        InputManager._trigger_key(self.callbacks_mouse_released, button)

    def trigger_mouse_scroll(self, scroll):
        for entity, func in self.callbacks_mouse_scroll:
            if entity in GameManager().entities:
                func(scroll)

    def clear(self):
        self.callbacks_key_down.clear()
        self.callbacks_key_up.clear()
        self.callbacks_mouse_pressed.clear()
        self.callbacks_mouse_scroll.clear()
        return self

    def update(self):
        """
        returns True if got a quit event
        """
        if self.update_callbacks_entities_order:
            self.update_callbacks_order()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return True
            elif event.type == pygame.KEYDOWN:
                self.trigger_key_down(event.key)

            elif event.type == pygame.KEYUP:
                self.trigger_key_up(event.key)
                if GameManager().debug and pygame.key.get_mods() & pygame.KMOD_CTRL:
                    GameManager().on_ctrl_d()

            elif event.type == pygame.MOUSEBUTTONDOWN:
                self.trigger_mouse_pressed(event.button)

            elif event.type == pygame.MOUSEBUTTONUP:
                self.trigger_mouse_released(event.button)

            elif event.type == pygame.MOUSEWHEEL:
                self.trigger_mouse_scroll(Vector2(event.precise_x, event.precise_y))
        return False


class ColliderManager(metaclass=Singelton):
    class Graph:
        def __init__(self):
            self.nodes: dict[type, list[Entity]] = {}
            self.edges: dict[type, set[type]] = {}

        def add_node(self, entity: Entity):
            if type(entity) not in self.nodes:
                self.nodes[type(entity)] = []
            self.nodes[type(entity)].append(entity)

        def remove_node(self, entity: Entity):
            self.nodes[type(entity)].remove(entity)

        def connect(self, type_a: type, type_b: type):
            if type_a not in self.edges:
                self.edges[type_a] = set()
            self.edges[type_a].add(type_b)

    def __init__(self):
        super().__init__()
        self.graph = ColliderManager.Graph()
        self.collision_functions_dict: dict[tuple[type, type], CollisionFunction] = {}

    def register(self, entity: Entity):
        self.graph.add_node(entity)

    def unregister(self, entity: Entity):
        self.graph.remove_node(entity)

    def describe_collision(
        self,
        entity_type: type,
        other_entity_type: type,
        check_collision: CollisionFunction,
    ):
        assert (
            CollideEntity in entity_type.mro()
            and CollideEntity in other_entity_type.mro()
        ), "Both types must inherit from CollideEntity"
        self.graph.connect(entity_type, other_entity_type)
        self.collision_functions_dict[(entity_type, other_entity_type)] = (
            check_collision
        )

    def update(self):
        for entity_type in self.graph.edges:
            for other_entity_type in self.graph.edges[entity_type]:
                if entity_type in self.graph.nodes:
                    for entity in self.graph.nodes[entity_type]:
                        if other_entity_type in self.graph.nodes:
                            for other_entity in self.graph.nodes[other_entity_type]:
                                self.collision_functions_dict[
                                    (entity_type, other_entity_type)
                                ](entity, other_entity)


class EmptyEntity(Entity):
    def render(self, sur: Surface):
        sur.fill(Color("Yellow"))

T = TypeVar('T')

@dataclass
class BarData:
    xs: List[str]
    ys: List[float]


class GameManager(metaclass=Singelton):
    DEBUG_INFO_DISPLAY_W = 500
    DEBUG_INFO_DISPLAY_H = 500

    @dataclass
    class DebugInfoElement:
        update_info: BarData
        render_info: BarData

    def __init__(self):
        self.entities: set[Entity] = set()
        self.clock = pygame.time.Clock()
        self.dt = 0
        self.fps = 60
        self.should_exit = False
        self.to_destroy: list[Entity] = []
        self.to_add: list[Entity] = []
        if not pygame.font.get_init():
            pygame.font.init()
        self.font = pygame.font.Font(size=20)
        self.debug = False
        self.debug_info_process: multiprocessing.Process = None
        self.debug_info_queue = multiprocessing.Queue(10)

    @overload
    def instatiate(self, __entity: T) -> T: ...
    @overload
    def instatiate(self, *entities: T) -> List[T]: ...

    def instatiate(self, *entities: T) -> Union[T, List[T]]:
        """
        Add entity to the scene
        """
        for entity in entities:
            assert (
                entity.state == EntityState.Initialized
            ), f"Have you initialized super() in {type(entity).__name__} contractor?"

            self.to_add.append(entity)
        if len(entities) == 1:
            return entities[0]
        return entities

    def destroy(self, *entities: Entity):
        """
        Remove entity from the scene
        """
        for entity in entities:
            self.to_destroy.append(entity)

    def clear_scene(self, exceptions: Set[Entity] = None):
        InputManager().clear()
        entities = self.entities
        if exceptions:
            entities = (e for e in entities if e not in exceptions)
        self.destroy(*entities)

    def update(self):
        should_quit = InputManager().update()

        self.should_exit |= should_quit

        UpdateManager().update(self.dt)

        for entity in self.to_destroy:
            if entity in self.entities:
                self.entities.remove(entity)
                entity.kill()  # self.to_destroy may expand here and it's fine
        self.to_destroy.clear()
        for entity in self.to_add:
            if entity not in self.entities:
                self.entities.add(entity)
                entity.start()  # self.to_add may expand here and it's fine

        self.to_add.clear()

        if self.debug:
            debug_info_element = GameManager.DebugInfoElement(
                update_info=BarData(
                    xs=[type(e).__name__ for e in UpdateManager().debug_info.keys()],
                    ys=list(UpdateManager().debug_info.values()),
                ),
                render_info=BarData(
                    xs=[type(e).__name__ for e in RenderManager().debug_info.keys()],
                    ys=list(RenderManager().debug_info.values()),
                ),
            )
            try:
                self.debug_info_queue.put(debug_info_element, block=False)
            except multiprocessing.queues.Full:
                pass
        if (
            self.should_exit
            and self.debug_info_process
            and self.debug_info_process.is_alive()
        ):
            self.debug_info_process.terminate()
            self.debug_info_process.join()

    def render(self, sur: Surface):
        RenderManager().render(sur)
        self.dt = self.clock.tick(self.fps) / 1000.0
        if self.debug:
            self.render_debug(sur)

    def render_debug(self, sur: Surface):
        for entity in self.entities:
            entity.render_debug(sur)

        fps_sur = self.font.render(str(int(self.clock.get_fps())), False, Color("Grey"))
        horz_pad = 10
        entities_count_sur = self.font.render(
            str(len(self.entities)), False, Color("Grey")
        )
        sur.blit(
            fps_sur,
            Vector2(sur.get_rect().topright) + Vector2Left() * fps_sur.get_width(),
        )
        sur.blit(
            entities_count_sur,
            Vector2(sur.get_rect().topright)
            + Vector2Left() * fps_sur.get_width()
            + Vector2Left() * horz_pad
            + Vector2Left() * entities_count_sur.get_width(),
        )

    def on_ctrl_d(self):
        if self.debug_info_process is None or not self.debug_info_process.is_alive():
            self.debug_info_process = multiprocessing.Process(
                target=self.debug_info_process_loop,
                args=(self.debug_info_queue,),
            )
            self.debug_info_process.start()

    @staticmethod
    def debug_info_process_loop(debug_info_queue: multiprocessing.Queue):
        from .barplot import BarPlot

        bg = Color("Black")
        pygame.init()
        display = pygame.display.set_mode(
            (GameManager.DEBUG_INFO_DISPLAY_W, GameManager.DEBUG_INFO_DISPLAY_H),
            flags=pygame.RESIZABLE,
        )
        pygame.display.set_caption("Debug info")

        barplot_size = Size(display.get_width(), display.get_height() / 2)

        update_debug_barplot = GameManager().instatiate(
            BarPlot(Pos(), barplot_size, [], [], "update time per entity ns")
        )
        render_debug_barplot = GameManager().instatiate(
            BarPlot(
                Pos(0, display.get_height() / 2),
                barplot_size,
                [],
                [],
                "render time per entity ns",
            )
        )
        # GameManager().debug = True  # OK now I just fck around
        while not GameManager().should_exit:
            barplot_size.w = display.get_width()
            barplot_size.h = display.get_height() / 2
            render_debug_barplot.transform.pos.y = display.get_height() / 2
            display.fill(bg)
            try:
                current_debug_info: GameManager.DebugInfoElement = (
                    debug_info_queue.get_nowait()
                )
                update_debug_barplot.xs = current_debug_info.update_info.xs
                update_debug_barplot.ys = current_debug_info.update_info.ys
                render_debug_barplot.xs = current_debug_info.render_info.xs
                render_debug_barplot.ys = current_debug_info.render_info.ys
            except multiprocessing.queues.Empty:
                pass
            GameManager().update()
            GameManager().render(display)
            pygame.display.flip()
        pygame.quit()


class UiButton(Entity):
    UI_DEFAULT_Z_INDEX = 100

    @dataclass
    class RenderData:
        color: Color
        color_hover: Color
        font: pygame.font.Font

    def __init__(self):
        super().__init__()
        self.text = ""
        self.render_data = UiButton.RenderData(
            Color("White"), Color("Blue"), GameManager().font
        )
        self.z_index = UiButton.UI_DEFAULT_Z_INDEX
        self.hovered = False
        self.pressed = False

    def start(self):
        super().start()
        InputManager().register_mouse_pressed(
            pygame.BUTTON_LEFT,
            self,
            lambda: self.on_left_click() if self.check_hover() else None,
        )
        InputManager().register_mouse_released(
            pygame.BUTTON_LEFT,
            self,
            lambda: self.on_mouse_released() if self.check_hover() else None,
        )

    def on_hover(self):
        pass

    def on_hover_out(self):
        pass

    def check_hover(self) -> bool:
        mouse_pos = pygame.mouse.get_pos()
        return self.transform.rect().collidepoint(mouse_pos)

    def on_left_click(self):
        self.pressed = True

    def on_mouse_released(self):
        self.pressed = False

    def update(self, dt):
        super().update(dt)
        if self.check_hover():
            self.hovered = True
            self.on_hover()
        elif self.hovered == True:
            self.hovered = False
            self.on_hover_out()

    def get_text_sur(self):
        text_color = self.render_data.color_hover
        if self.check_hover():
            text_color = self.render_data.color
        return self.render_data.font.render(self.text, True, text_color)

    def render_text(self, sur: Surface):
        text_sur = self.get_text_sur()
        sur.blit(text_sur, self.transform.center - Size(text_sur.get_size()) / 2)

    def render(self, sur: Surface):
        color = self.render_data.color
        if self.check_hover():
            color = self.render_data.color_hover
        pygame.draw.rect(sur, color, self.transform.rect())
        self.render_text(sur)


class AnimationType(Enum):
    Linear = 0
    Sin = 1
    EaseOutElastic = 2
    EaseOutBounce = 3
    EaseInOutBack = 4


class Animation(Entity):
    def __init__(
        self,
        duration_secs,
        animation_type: AnimationType = AnimationType.Linear,
        repeat=False,
    ):
        super().__init__()
        self.duration = duration_secs
        self.timer = 0
        self.animation_func = Animation.get_animation_func(animation_type)
        self.repeat = repeat
        self.should_play = True

    def reset_animation(self):
        self.timer = 0
        self.should_play = True

    def update(self, dt):
        super().update(dt)
        if self.should_play:
            self.timer += dt
            if self.timer > self.duration:
                self.reset_animation()
                if not self.repeat:
                    self.should_play = False
            else:
                self.animation_frame(self.animation_func(self.timer / self.duration))

    def animation_frame(self, x):
        pass

    @staticmethod
    def get_animation_func(animation_type: AnimationType):
        def ease_out_elastic(x):
            c4 = (2 * pi) / 3
            if x == 0 or x == 1:
                return x
            return pow(2, -10 * x) * sin((x * 10 - 0.75) * c4) + 1

        def ease_out_bounce(x: float):
            n1 = 7.5625
            d1 = 2.75

            if x < 1 / d1:
                return n1 * x * x
            elif x < 2 / d1:
                x -= 1.5 / d1
                return n1 * x * x + 0.75
            elif x < 2.5 / d1:
                x -= 2.25 / d1
                return n1 * x * x + 0.9375
            else:
                x -= 2.625 / d1
                return n1 * x * x + 0.984375

        def ease_in_out_back(x: float):
            c1 = 1.70158
            c2 = c1 * 1.525
            return (
                (pow(2 * x, 2) * ((c2 + 1) * 2 * x - c2)) / 2
                if x < 0.5
                else (pow(2 * x - 2, 2) * ((c2 + 1) * (x * 2 - 2) + c2) + 2) / 2
            )

        if animation_type == AnimationType.Linear:
            return lambda x: x
        elif animation_type == AnimationType.Sin:
            return lambda x: sin(pi * x)
        elif animation_type == AnimationType.EaseOutBounce:
            return ease_out_bounce
        elif animation_type == AnimationType.EaseInOutBack:
            return ease_in_out_back
        else:
            assert animation_type == AnimationType.EaseOutElastic
            return ease_out_elastic


class SingeltonEntity(Entity, metaclass=Singelton):
    def __init__(self):
        super().__init__()
        GameManager().instatiate(self)

    def kill(self):
        super().kill()
        self.state = EntityState.Initialized
        GameManager().instatiate(self)
