import random

import pymunk

from physics.world import CollisionCategories


class PhysicsObjectType:
    CRATE = "crate"
    LOG = "log"
    ROCK = "rock"


class PhysicsObject:
    def __init__(self, x, y, obj_type, space):
        self.x = x
        self.y = y
        self.type = obj_type
        self.active = True
        self.body = None
        self.shapes = []
        self._create(space)

    def _create(self, space):
        if self.type == PhysicsObjectType.CRATE:
            w, h = 0.5, 0.5
            mass = 20.0
            moment = pymunk.moment_for_box(mass, (w, h))
            self.body = pymunk.Body(mass, moment)
            self.body.position = (self.x, self.y)
            space.add(self.body)
            shape = pymunk.Poly.create_box(self.body, (w, h))
            shape.friction = 0.6
            shape.elasticity = 0.05
            shape.collision_type = CollisionCategories.PICKUP
            shape.filter = pymunk.ShapeFilter(
                categories=CollisionCategories.PICKUP,
                mask=CollisionCategories.CHASSIS | CollisionCategories.WHEEL | CollisionCategories.TERRAIN,
            )
            space.add(shape)
            self.shapes.append(shape)
            self.width, self.height = w, h

        elif self.type == PhysicsObjectType.LOG:
            length, radius = 1.2, 0.2
            mass = 35.0
            moment = pymunk.moment_for_box(mass, (length, radius * 2))
            self.body = pymunk.Body(mass, moment)
            self.body.position = (self.x, self.y)
            space.add(self.body)
            shape = pymunk.Poly.create_box(self.body, (length, radius * 2))
            shape.friction = 0.8
            shape.elasticity = 0.1
            shape.collision_type = CollisionCategories.PICKUP
            shape.filter = pymunk.ShapeFilter(
                categories=CollisionCategories.PICKUP,
                mask=CollisionCategories.CHASSIS | CollisionCategories.WHEEL | CollisionCategories.TERRAIN,
            )
            space.add(shape)
            self.shapes.append(shape)
            self.width, self.height = length, radius * 2

        elif self.type == PhysicsObjectType.ROCK:
            radius = 0.25 + random.random() * 0.2
            mass = 50.0 * (radius / 0.35)
            moment = pymunk.moment_for_circle(mass, 0, radius)
            self.body = pymunk.Body(mass, moment)
            self.body.position = (self.x, self.y)
            space.add(self.body)
            shape = pymunk.Circle(self.body, radius)
            shape.friction = 0.9
            shape.elasticity = 0.05
            shape.collision_type = CollisionCategories.PICKUP
            shape.filter = pymunk.ShapeFilter(
                categories=CollisionCategories.PICKUP,
                mask=CollisionCategories.CHASSIS | CollisionCategories.WHEEL | CollisionCategories.TERRAIN,
            )
            space.add(shape)
            self.shapes.append(shape)
            self.width = self.height = radius * 2

    def is_active(self):
        return self.active

    def dispose(self, space):
        for s in self.shapes:
            space.remove(s)
        if self.body:
            space.remove(self.body)
        self.shapes.clear()
        self.body = None
        self.active = False
