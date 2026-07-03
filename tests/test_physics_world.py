import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from physics.world import CollisionCategories, PhysicsWorld


def test_physics_world_creation():
    world = PhysicsWorld()
    assert world.space.gravity.y == -30.0
    assert world.space.damping == 0.98


def test_add_and_remove_body():
    import pymunk

    world = PhysicsWorld()
    body = pymunk.Body(1, 1)
    body.position = (0, 5)
    world.add_body(body)
    assert body in world.bodies

    world.remove_body(body)
    assert body not in world.bodies


def test_add_and_remove_shape():
    import pymunk

    world = PhysicsWorld()
    body = pymunk.Body(body_type=pymunk.Body.STATIC)
    world.add_body(body)
    shape = pymunk.Segment(body, (0, 0), (10, 0), 0.1)
    world.add_shape(shape)
    assert shape in world.shapes

    world.remove_shape(shape)
    assert shape not in world.shapes


def test_add_and_remove_constraint():
    import pymunk

    world = PhysicsWorld()
    b1 = pymunk.Body(1, 1)
    b2 = pymunk.Body(1, 1)
    world.add_body(b1)
    world.add_body(b2)
    constraint = pymunk.DampedSpring(b1, b2, (0, 0), (0, 0), 1, 10, 1)
    world.add_constraint(constraint)
    assert constraint in world.constraints

    world.remove_constraint(constraint)
    assert constraint not in world.constraints


def test_clear():
    import pymunk

    world = PhysicsWorld()
    b1 = pymunk.Body(1, 1)
    world.add_body(b1)
    shape = pymunk.Segment(world.space.static_body, (0, 0), (5, 0), 0.1)
    world.add_shape(shape)
    b2 = pymunk.Body(2, 2)
    world.add_body(b2)
    joint = pymunk.PinJoint(b1, b2)
    world.add_constraint(joint)

    world.clear()
    assert len(world.bodies) == 0
    assert len(world.shapes) == 0
    assert len(world.constraints) == 0
    assert len(world._contacting_pairs) == 0


def test_body_contact_detection():
    import pymunk

    world = PhysicsWorld()

    static_body = world.space.static_body
    ground = pymunk.Segment(static_body, (-100, 0), (100, 0), 0.1)
    ground.collision_type = CollisionCategories.TERRAIN
    world.add_shape(ground)

    wheel_body = pymunk.Body(1, 1)
    wheel_body.position = (0, 0.5)
    world.add_body(wheel_body)
    wheel_shape = pymunk.Circle(wheel_body, 0.3)
    wheel_shape.collision_type = CollisionCategories.WHEEL
    world.add_shape(wheel_shape)

    for _ in range(10):
        world.space.step(1 / 60)

    assert world.body_has_contacts(wheel_body) is True
