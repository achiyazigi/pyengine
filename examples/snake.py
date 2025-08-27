import pygame
from pygame import Color, K_UP, K_DOWN, K_LEFT, K_RIGHT, K_ESCAPE
from pygame.math import Vector2
from random import randint
from pyengine import *

# Constants for the game window and grid
W = 640
H = 480
GRID_SIZE = 20
BG_COLOR = Color(30, 30, 30)

# Directions for the snake
UP = Vector2(0, -1)
DOWN = Vector2(0, 1)
LEFT = Vector2(-1, 0)
RIGHT = Vector2(1, 0)


# A singleton class to manage the game state, score, and game over logic.
# Inheriting from SingeltonEntity handles the instance lifecycle correctly.
class SnakeGameManager(SingeltonEntity):
    def __init__(self):
        super().__init__()
        self.score = 0
        self.running = True
        self.game_over_screen = None
        self.z_index = -100  # Render behind everything else

    def start_game(self):
        # Clear the entire scene to ensure all old entities are removed.
        GameManager().clear_scene(exceptions={self})

        self.score = 0
        self.running = True
        self.game_over_screen = None

        # Instantiate the essential game objects for a new game.
        snake = Snake()
        apple = Apple(snake)
        GameManager().instatiate(snake, apple, ScoreDisplay())

    def end_game(self):
        if self.running:
            self.running = False
            self.game_over_screen = GameManager().instatiate(GameOverScreen(self.score))

    def update(self, dt):
        super().update(dt)
        if not self.running:
            return


# The Apple entity that the snake eats.
class Apple(CollideEntity):
    def __init__(self, snake: "Snake"):
        super().__init__()
        self.transform.size = Size(GRID_SIZE, GRID_SIZE)
        self.color = Color("red")
        self.randomize_position(snake)

    # Move the apple to a new random position on the grid.
    def randomize_position(self, snake: "Snake"):
        while True:
            self.transform.pos.x = randint(0, W // GRID_SIZE - 1) * GRID_SIZE
            self.transform.pos.y = randint(0, H // GRID_SIZE - 1) * GRID_SIZE

            # Check for collision with the head
            if self.transform.rect().colliderect(snake.transform.rect()):
                continue

            # Check for collision with the body segments
            collision = False
            for segment in snake.segments:
                if self.transform.rect().colliderect(segment.transform.rect()):
                    collision = True
                    break

            if not collision:
                break

    def render(self, sur):
        pygame.draw.rect(sur, self.color, self.transform.rect())

    # Register collision with the snake head.
    @classmethod
    def register_collision_functions(cls):
        return [CollisionData(Snake, Apple.on_snake_collision)]

    # When the snake collides with the apple, the snake grows and the apple moves.
    @staticmethod
    def on_snake_collision(apple: "Apple", snake: "Snake"):
        # The snake object itself is now the head, so we check collision with its transform.
        if apple.transform.rect().colliderect(snake.transform.rect()):
            snake.grow_pending = True
            apple.randomize_position(snake)
            SnakeGameManager().score += 1


# A segment of the snake's body.
class SnakeSegment(Entity):
    def __init__(self, pos, color):
        super().__init__()
        self.transform.size = Size(GRID_SIZE, GRID_SIZE)
        self.transform.pos = pos
        self.color = color

    def render(self, sur):
        pygame.draw.rect(sur, self.color, self.transform.rect())


# The main snake class.
class Snake(CollideEntity):
    def __init__(self):
        super().__init__()
        self.transform.size = Size(GRID_SIZE, GRID_SIZE)
        self.transform.pos = Pos(W / 2, H / 2)
        self.speed = GRID_SIZE
        self.direction = RIGHT
        self.next_direction = None  # New variable to queue the next direction
        self.segments = []  # This list now only contains SnakeSegment objects
        self.grow_pending = False
        self.last_update_time = pygame.time.get_ticks()
        self.update_interval = 200  # milliseconds

        # Register input handlers for arrow keys.
        InputManager().register_key_down(K_UP, self, lambda: self.set_direction(UP))
        InputManager().register_key_down(K_DOWN, self, lambda: self.set_direction(DOWN))
        InputManager().register_key_down(K_LEFT, self, lambda: self.set_direction(LEFT))
        InputManager().register_key_down(
            K_RIGHT, self, lambda: self.set_direction(RIGHT)
        )

    def start(self):
        super().start()
        self.z_index = 1

    def set_direction(self, new_dir):
        # Only queue a new direction if it's not a direct reversal of the current direction.
        if new_dir + self.direction != Vector2(0, 0):
            self.next_direction = new_dir

    def update(self, dt):
        super().update(dt)
        if not SnakeGameManager().running:
            return

        current_time = pygame.time.get_ticks()
        if current_time - self.last_update_time > self.update_interval:
            self.last_update_time = current_time
            self.move()

    def move(self):
        # Apply the queued direction change, if any.
        if self.next_direction is not None:
            self.direction = self.next_direction
            self.next_direction = None

        # Check for wall collision first
        if not (
            0 <= self.transform.pos.x + self.direction.x * self.speed < W
            and 0 <= self.transform.pos.y + self.direction.y * self.speed < H
        ):
            SnakeGameManager().end_game()
            return

        # Check for self-collision before moving the head
        for segment in self.segments:
            if segment.transform.rect().colliderect(
                pygame.Rect(
                    self.transform.pos + self.direction * self.speed,
                    self.transform.size,
                )
            ):
                SnakeGameManager().end_game()
                return

        # Create a new segment at the head's current position before it moves
        new_segment = SnakeSegment(self.transform.pos.copy(), Color("green"))
        self.segments.insert(0, new_segment)
        GameManager().instatiate(new_segment)

        # Now update the head's position
        self.transform.pos += self.direction * self.speed

        # Remove the tail if not growing
        if self.grow_pending:
            self.grow_pending = False
            self.update_interval = max(50, self.update_interval - 5)
        else:
            if len(self.segments) > 1:
                tail = self.segments.pop()
                GameManager().destroy(tail)

    def fixed_update(self, fixed_dt):
        super().fixed_update(fixed_dt)
        # Collision detection is now handled in the move method.
        pass

    def render(self, sur):
        # The segments are rendered by their own entities. We render the head here.
        pygame.draw.rect(sur, Color("green"), self.transform.rect())


# Display the current score.
class ScoreDisplay(Entity):
    def __init__(self):
        super().__init__()
        self.transform.pos = Pos(10, 10)
        self.font = pygame.font.Font(None, 36)

    def render(self, sur):
        score_text = f"Score: {SnakeGameManager().score}"
        text_surface = self.font.render(score_text, True, Color("white"))
        sur.blit(text_surface, self.transform.pos)


# The game over screen.
class GameOverScreen(Entity):
    def __init__(self, final_score):
        super().__init__()
        self.final_score = final_score
        self.z_index = 100  # Render on top of everything
        self.font_large = pygame.font.Font(None, 72)
        self.font_medium = pygame.font.Font(None, 48)
        InputManager().register_key_down(K_ESCAPE, self, self.restart_game)

    def restart_game(self):
        SnakeGameManager().start_game()
        return True  # Stop propagation

    def render(self, sur):
        # Draw a semi-transparent overlay
        overlay = pygame.Surface((W, H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 128))
        sur.blit(overlay, (0, 0))

        # Render "Game Over" text
        game_over_text = self.font_large.render("Game Over", True, Color("white"))
        text_rect = game_over_text.get_rect(center=(W / 2, H / 2 - 50))
        sur.blit(game_over_text, text_rect)

        # Render final score
        score_text = self.font_medium.render(
            f"Final Score: {self.final_score}", True, Color("white")
        )
        score_rect = score_text.get_rect(center=(W / 2, H / 2 + 20))
        sur.blit(score_text, score_rect)

        # Render restart instructions
        restart_text = self.font_medium.render(
            "Press 'Esc' to Restart", True, Color("white")
        )
        restart_rect = restart_text.get_rect(center=(W / 2, H / 2 + 100))
        sur.blit(restart_text, restart_rect)


# Main game loop setup
def main():
    pygame.init()
    pygame.display.set_caption("Snake")
    screen = pygame.display.set_mode((W, H))

    SnakeGameManager().start_game()

    # Start the fixed update loop for collision detection and movement
    UpdateManager.FIXED_DT = 0.1
    UpdateManager().start_fixed_update_loop()
    GameManager().debug = True
    while not GameManager().should_exit:
        screen.fill(BG_COLOR)
        GameManager().update()
        GameManager().render(screen)
        pygame.display.flip()

    UpdateManager().stop_fixed_update_loop()
    pygame.quit()


if __name__ == "__main__":
    main()
