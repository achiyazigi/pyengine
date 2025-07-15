import unittest
from unittest.mock import Mock, patch
import pygame
from pyengine import (
    Entity,
    EntityState,
    GameManager,
    UpdateManager,
    RenderManager,
    InputManager,
    ColliderManager,
    UiButton,
    Animation,
    AnimationType,
    CollideEntity,
    Vector2,
)


class BaseTestWithCleanup(unittest.TestCase):
    def setUp(self):
        super().setUp()
        display = pygame.display.set_mode((1, 1))

    def tearDown(self):
        self.clear_scene()

    def clear_scene(self):
        GameManager().clear_scene()
        GameManager().update()


class TestEntityLifecycle(BaseTestWithCleanup):
    def setUp(self):
        pygame.init()
        self.entity = Entity()
        self.surface = Mock()

    def test_entity_initial_state(self):
        self.assertEqual(self.entity.state, EntityState.Initialized)

    def test_entity_start(self):
        gm = GameManager()
        gm.instatiate(self.entity)
        gm.update()
        self.assertEqual(self.entity.state, EntityState.Started)

    def test_entity_kill(self):
        gm = GameManager()
        gm.instatiate(self.entity)
        gm.update()
        gm.destroy(self.entity)
        gm.update()
        self.assertEqual(self.entity.state, EntityState.Destroyed)


class TestManagerRegistration(unittest.TestCase):
    def setUp(self):
        pygame.init()
        self.entity = Entity()

    def tearDown(self):
        UpdateManager().unregister(self.entity)
        return super().tearDown()

    def test_update_manager_register_unregister(self):
        manager = UpdateManager()
        manager.register(self.entity)
        self.assertIn(self.entity, manager.entityes_sorted)
        manager.unregister(self.entity)
        self.assertNotIn(self.entity, manager.entityes_sorted)

    def test_render_manager_register_unregister(self):
        manager = RenderManager()
        manager.register(self.entity)
        self.assertIn(self.entity, manager.entityes_sorted)
        manager.unregister(self.entity)
        self.assertNotIn(self.entity, manager.entityes_sorted)


class TestUiButtonHover(unittest.TestCase):
    def setUp(self):
        pygame.init()
        self.button = UiButton()
        self.button.transform.pos = pygame.Vector2(0, 0)
        self.button.transform.size = pygame.Vector2(100, 50)

    @patch("pygame.mouse.get_pos")
    def test_hover_inside_button(self, mock_mouse_pos):
        mock_mouse_pos.return_value = (10, 10)
        self.assertTrue(self.button.check_hover())

    @patch("pygame.mouse.get_pos")
    def test_hover_outside_button(self, mock_mouse_pos):
        mock_mouse_pos.return_value = (200, 200)
        self.assertFalse(self.button.check_hover())


class TestAnimation(BaseTestWithCleanup):
    def test_linear_animation(self):
        anim = Animation(1.0, AnimationType.Linear, repeat=False)
        anim.animation_frame = Mock()
        GameManager().instatiate(anim)
        anim.update(0.5)
        anim.animation_frame.assert_called_once()
        self.assertTrue(anim.should_play)
        anim.update(0.6)
        self.assertFalse(anim.should_play)  # animation should stop


class TestInputManager(BaseTestWithCleanup):
    def setUp(self):
        pygame.init()
        self.entity = Entity()
        self.called = False

    def callback(self):
        self.called = True

    def test_key_down_callback(self):
        im = InputManager()
        im.clear()
        im.register_key_down(pygame.K_a, self.entity, self.callback)
        GameManager().instatiate(self.entity)
        GameManager().update()
        im.trigger_key_down(pygame.K_a)
        self.assertTrue(self.called)


class TestColliderManager(unittest.TestCase):

    class A(CollideEntity):
        pass

    class B(CollideEntity):
        pass

    def setUp(self):
        self.a = TestColliderManager.A()
        self.b = TestColliderManager.B()
        super().setUp()

    def tearDown(self):
        ColliderManager().unregister(self.a)
        ColliderManager().unregister(self.b)
        return super().tearDown()

    def test_collision_function_called(self):

        was_called = []

        def collide_func(e1, e2):
            was_called.append(True)

        ColliderManager().describe_collision(
            TestColliderManager.A, TestColliderManager.B, collide_func
        )
        ColliderManager().register(self.a)
        ColliderManager().register(self.b)
        ColliderManager().update()
        self.assertTrue(any(was_called))


class TestSingletonBehavior(unittest.TestCase):
    def test_update_manager_singleton(self):
        a = UpdateManager()
        b = UpdateManager()
        self.assertIs(a, b)

    def test_render_manager_singleton(self):
        a = RenderManager()
        b = RenderManager()
        self.assertIs(a, b)

    def test_game_manager_singleton(self):
        a = GameManager()
        b = GameManager()
        self.assertIs(a, b)


class TestRenderSorting(BaseTestWithCleanup):

    def setUp(self):
        self.a = Entity()
        self.b = Entity()
        return super().setUp()

    def tearDown(self):
        RenderManager().unregister(self.a)
        RenderManager().unregister(self.b)
        return super().tearDown()

    def test_render_order(self):

        RenderManager().register(self.a)
        RenderManager().register(self.b)
        self.a.z_index = 2
        self.b.z_index = 1
        self.assertEqual(RenderManager().entityes_sorted, [self.b, self.a])
        self.a.z_index = 0
        self.assertEqual(RenderManager().entityes_sorted, [self.a, self.b])


class TestTransformParenting(unittest.TestCase):
    def test_child_follows_parent(self):
        parent = Entity()
        child = Entity()
        parent.transform.pos = Vector2(10, 0)
        child.set_parent(parent)
        initial = child.transform.pos.copy()
        parent.transform.pos = Vector2(20, 0)
        child.update(0)
        self.assertEqual(child.transform.pos, initial + Vector2(10, 0))


class TestCollisionGraph(unittest.TestCase):
    def test_graph_connect(self):
        cm = ColliderManager()

        class A(CollideEntity):
            pass

        class B(CollideEntity):
            pass

        self.a = A()
        self.b = B()
        called = []

        def on_collision(e1, e2):
            called.append(True)

        cm.describe_collision(A, B, on_collision)
        cm.register(self.a)
        cm.register(self.b)
        cm.update()
        self.assertTrue(any(called))
        self.assertIn(B, cm.graph.edges[A])

    def tearDown(self):
        ColliderManager().unregister(self.a)
        ColliderManager().unregister(self.b)
        return super().tearDown()


class TestUiButtonClick(BaseTestWithCleanup):
    def test_button_click(self):
        button = GameManager().instatiate(UiButton())
        button.transform.size = Vector2(100, 50)
        button.transform.pos = Vector2(0, 0)
        button.on_left_click = Mock()
        button.on_mouse_released = Mock()

        with patch("pygame.mouse.get_pos", return_value=(10, 10)):
            button.check_hover()  # called internally by update
            GameManager().update()
            InputManager().trigger_mouse_pressed(pygame.BUTTON_LEFT)

        button.on_left_click.assert_called_once()


class TestAnimationTypes(unittest.TestCase):
    def setUp(self):
        self.anim = Animation(1.0)

    def test_sin_function(self):
        func = self.anim.get_animation_func(AnimationType.Sin)
        result = func(0.5)
        self.assertAlmostEqual(result, 1.0, delta=0.1)

    def test_ease_out_elastic_bounds(self):
        func = self.anim.get_animation_func(AnimationType.EaseOutElastic)
        self.assertEqual(func(0), 0)
        self.assertEqual(func(1), 1)


class TestGameManagerIntegration(BaseTestWithCleanup):
    def test_instatiate_and_destroy(self):
        gm = GameManager()
        e = Entity()
        gm.instatiate(e)
        self.assertIn(e, gm.to_add)
        gm.update()
        self.assertIn(e, gm.entities)
        gm.destroy(e)
        self.assertIn(e, gm.to_destroy)
        gm.update()
        self.assertNotIn(e, gm.entities)
        self.assertEqual(e.state, EntityState.Destroyed)


if __name__ == "__main__":
    unittest.main()
