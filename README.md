# pyengine

Is an entity system and entity management for pygame

## Example:

```python
import pygame
from pygame import Color
from pyengine import *

W = 640
H = 512
BG = Color("Black")

# Entity representing a red square moving on the screen
class MovingSquare(Entity):
    SPEED = 50
    COLOR = Color("Red")
    def __init__(self, pos:Pos, size:float):
        super().__init__()
        # self.transform is defined in Entity
        # and represents the posisition and size of the entity
        self.transform.pos = pos
        self.transform.size = Size(size)

        self.dir = Vector2(1,1).normalize()

    # logic
    def update(self, dt):
        if self.transform.rect().left < 0:
            self.dir.x =1
        if self.transform.rect().right > W:
            self.dir.x = -1
        if self.transform.rect().top < 0:
            self.dir.y = 1
        if self.transform.rect().bottom > H:
            self.dir.y = -1
        self.dir.normalize_ip()

        self.transform.pos += self.dir*dt*MovingSquare.SPEED

    # art
    def render(self, sur):
        pygame.draw.rect(sur, MovingSquare.COLOR, self.transform.rect())


def main():
    pygame.init()
    pygame.display.set_caption("Title goes here")
    screen = pygame.display.set_mode((W, H))

    # Register the entity in the GameManager singleton.
    # The entity logic, render, and lifetime as well as inputs and collisions
    # will be managed by GameManager
    GameManager().instatiate(MovingSquare(Pos(),30))

    while not GameManager().should_exit:
        screen.fill(BG)
        # This will update all entities:
        GameManager().update()
        # This will render all entities:
        GameManager().render(screen)
        # # You can switch between render and render_debug to see more information about the entities. do not use both at once:
        # GameManager().render_debug(screen)
        pygame.display.flip()


if __name__ == "__main__":
    main()
    pygame.quit()

```

## Features

### Control render order

z_index will automatically update the render order of the entity.  
If 2 entities have the same z_index, they will be rendered in an arbitrary order between them.

```python
entity_on_the_back.z_index = 0
entity_up_front.z_index = 1
```

### Control update order

update_order will automatically update the update order of the entity.  
If 2 entities have the same update_order, they will be updated in an arbitrary order between them.

```python
entity_update_first.update_order = 0
entity_update_second.update_order = 1
```

### Register to input events

With InputManager you can register entities to input events.
When the entity is being destroyed, the InputManager unregister the listener.

```python
class MyEntity(Entity):
    def __init__(self):
        super().__init__()
        InputManager().register_mouse_released(
            pygame.BUTTON_LEFT, # button
            self, # entity
            self.on_mouse_release # function
        )
    def on_mouse_released(self):
        print("Mouse released")
```

### Register to collision management

pyengine has a graph based collision manager.  
When an entity derives from `CollideEntity`, its type is registered in the graph.
When another `CollideEntity` describes a collision with the specific type, the callback will only be called for those types.
Collision callbacks are being called from a fixed dt loop.
dont forget to start the fixed loop thread, the way you do it is included in this example:

```python
import pygame
from pygame import Color
from pyengine import *

W = 640
H = 512
BG = Color("Black")

class MovingSquare(CollideEntity):

    def __init__(self, pos:Pos, size:float, color:Color, speed:float):
        super().__init__()
        self.transform.pos = pos
        self.transform.size = Size(size)
        self.dir = Vector2(1,1).normalize()
        self.color = color
        self.speed = speed

    # defined in CollideEntity, override here:
    @classmethod
    def register_collision_functions(cls):
        super().register_collision_functions()
        return [CollisionData(MovingSquare, cls.on_collision_with_moving_square)]

    def on_collision_with_moving_square(self, other: 'MovingSquare'):
        if self is other:
            return
        if self.transform.rect().colliderect(other.transform.rect()):
            self.dir.x *= -1
            self.dir.y *= -1
            print(f"Collision detected between {self} and {other}. New direction: {self.dir}")

    def update(self, dt):
        if self.transform.rect().left < 0:
            self.dir.x =1
        if self.transform.rect().right > W:
            self.dir.x = -1
        if self.transform.rect().top < 0:
            self.dir.y = 1
        if self.transform.rect().bottom > H:
            self.dir.y = -1
        self.dir.normalize_ip()

        self.transform.pos += self.dir*dt*self.speed

    def render(self, sur):
        pygame.draw.rect(sur, self.color, self.transform.rect())


def main():
    pygame.init()
    pygame.display.set_caption("Template")
    screen = pygame.display.set_mode((W, H))

    GameManager().instatiate(
        MovingSquare(Pos(),30, Color("Red"),50),
        MovingSquare(Pos(100, 100), 30, Color("Blue"),30)
    )

    # Important! collisions will be checked in the fixed update loop.
    # You can control the interval with:
    UpdateManager().FIXED_DT = 0.01  # 10 updates per second
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

```

### Parenting

Attach an entity to a parent entity to keep the offset position from the parent.
[example](examples/parenting.py)

## Advanced

For more advanced examples and actuall games, check the [examples](exapmles) folder
