from dataclasses import dataclass
import pygame
from pygame import Color, Vector2, Surface, Rect
from pyengine import *

W = 800
H = 600
BG = Color("Black")
BALL_SPEED = 300
PADDLE_SPEED = 400
PADDLE_WIDTH = 20
PADDLE_HEIGHT = 100
BALL_SIZE = 15
PADDLE_PADDING = 30  # Distance of paddles from the screen edges


@dataclass
class Keys:
    up: int
    down: int


class ScoreDisplay(Entity):
    def __init__(self):
        super().__init__()
        self.left_score = 0
        self.right_score = 0
        self.font = pygame.font.Font(None, 74)

    def increment_left_score(self):
        self.left_score += 1

    def increment_right_score(self):
        self.right_score += 1

    def render(self, sur: Surface):
        left_score_text = self.font.render(str(self.left_score), True, Color("White"))
        right_score_text = self.font.render(str(self.right_score), True, Color("White"))
        sur.blit(left_score_text, (W // 4, 20))
        sur.blit(right_score_text, (3 * W // 4 - right_score_text.get_width(), 20))

class Paddle(CollideEntity):
    def __init__(self, pos: Pos, keys: Keys = None, ball: "Ball" = None):
        super().__init__()
        self.transform.pos = pos
        self.transform.size = Size(PADDLE_WIDTH, PADDLE_HEIGHT)
        self.color = Color("White")
        self.keys = keys
        self.ball = ball
        self.velocity = 0
        self.smooth_factor = 0.1  # Controls how smoothly the AI paddle moves

    def start(self):
        super().start()
        if self.keys:
            InputManager().register_key_down(self.keys.up, self, lambda: self.set_velocity(-PADDLE_SPEED))
            InputManager().register_key_down(self.keys.down, self, lambda: self.set_velocity(PADDLE_SPEED))
            InputManager().register_key_up(self.keys.up, self, lambda: self.set_velocity(0))
            InputManager().register_key_up(self.keys.down, self, lambda: self.set_velocity(0))

    def set_velocity(self, velocity):
        self.velocity = velocity

    def update(self, dt):
        if self.keys:
            # Player-controlled paddle
            self.transform.pos.y += self.velocity * dt
        elif self.ball:
            # Smarter AI-controlled paddle with smoother movement
            ball_future_y = self.predict_ball_position()
            target_y = ball_future_y - PADDLE_HEIGHT / 2
            self.transform.pos.y += (target_y - self.transform.pos.y) * self.smooth_factor

        self.transform.pos.y = pygame.math.clamp(self.transform.pos.y, 0, H - PADDLE_HEIGHT)

    def predict_ball_position(self):
        """
        Predicts the ball's future y-position when it reaches the paddle's x-position.
        """
        if self.ball.velocity.x == 0:
            return self.ball.transform.pos.y

        time_to_reach_paddle = abs((self.transform.pos.x - self.ball.transform.pos.x) / self.ball.velocity.x)
        predicted_y = self.ball.transform.pos.y + self.ball.velocity.y * time_to_reach_paddle

        # Handle ball bouncing off the top and bottom walls
        while predicted_y < 0 or predicted_y > H:
            if predicted_y < 0:
                predicted_y = -predicted_y
            elif predicted_y > H:
                predicted_y = 2 * H - predicted_y

        return predicted_y

    def render(self, sur: Surface):
        pygame.draw.rect(sur, self.color, self.transform.rect())

class Ball(CollideEntity):
    def __init__(self, score_display: ScoreDisplay):
        super().__init__()
        self.transform.size = Size(BALL_SIZE, BALL_SIZE)
        self.transform.pos = Pos(W / 2 - BALL_SIZE / 2, H / 2 - BALL_SIZE / 2)
        self.velocity = Vector2(BALL_SPEED, BALL_SPEED).normalize() * BALL_SPEED
        self.color = Color("White")
        self.score_display = score_display

    @classmethod
    def register_collision_functions(cls):
        return [CollisionData(Paddle, cls.on_collision_with_paddle)]

    @staticmethod
    def on_collision_with_paddle(ball: "Ball", paddle: Paddle):
        if ball.transform.rect().colliderect(paddle.transform.rect()):
            ball.velocity.x *= -1
            ball.velocity.y += (ball.transform.center.y - paddle.transform.center.y) * 2

    def update(self, dt):
        self.transform.pos += self.velocity * dt

        if self.transform.rect().top <= 0 or self.transform.rect().bottom >= H:
            self.velocity.y *= -1

        if self.transform.rect().left < PADDLE_PADDING + PADDLE_WIDTH / 2:
            self.score_display.increment_right_score()
            self.reset_position()
        elif self.transform.rect().right > W - (PADDLE_PADDING + PADDLE_WIDTH / 2):
            self.score_display.increment_left_score()
            self.reset_position()

    def reset_position(self):
        self.transform.pos = Pos(W / 2 - BALL_SIZE / 2, H / 2 - BALL_SIZE / 2)
        self.velocity = Vector2(BALL_SPEED, BALL_SPEED).normalize() * BALL_SPEED

    def render(self, sur: Surface):
        pygame.draw.ellipse(sur, self.color, self.transform.rect())


def start_game_scene():
    GameManager().clear_scene()
    score_display = GameManager().instatiate(ScoreDisplay())
    ball = GameManager().instatiate(Ball(score_display))
    GameManager().instatiate(
        Paddle(Pos(PADDLE_PADDING, H / 2 - PADDLE_HEIGHT / 2), ball=ball),
        Paddle(Pos(W - PADDLE_PADDING - PADDLE_WIDTH, H / 2 - PADDLE_HEIGHT / 2), Keys(pygame.K_UP, pygame.K_DOWN)),
        ball
    )


def main():
    start_game_scene()

    pygame.init()
    pygame.display.set_caption("Pong")
    screen = pygame.display.set_mode((W, H))

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