import pymunk

from constants import GRAVITY


class CollisionCategories:
    TERRAIN = 1
    CHASSIS = 2
    WHEEL = 4
    PICKUP = 8


class PhysicsWorld:
    def __init__(self):
        self.space = pymunk.Space()
        self.space.gravity = (0, GRAVITY)
        self.space.collision_slop = 0.01
        self.space.idle_speed_threshold = 1.0
        self.space.damping = 0.98
        self.bodies = []
        self.shapes = []
        self.constraints = []
        self._contacting_pairs = set()
        self._setup_collision_handlers()

    def _setup_collision_handlers(self):
        def _begin(arbiter, space, data):
            s1, s2 = arbiter.shapes
            self._contacting_pairs.add((s1, s2))

        def _separate(arbiter, space, data):
            s1, s2 = arbiter.shapes
            self._contacting_pairs.discard((s1, s2))

        self.space.on_collision(
            CollisionCategories.WHEEL,
            CollisionCategories.TERRAIN,
            begin=_begin,
            separate=_separate,
        )
        self.space.on_collision(
            CollisionCategories.CHASSIS,
            CollisionCategories.TERRAIN,
            begin=_begin,
            separate=_separate,
        )

    def body_has_contacts(self, body):
        if not body.shapes:
            return False
        body_shapes = set(body.shapes)
        for s1, s2 in self._contacting_pairs:
            if s1 in body_shapes or s2 in body_shapes:
                return True
        return False

    def add_body(self, body):
        self.space.add(body)
        self.bodies.append(body)

    def add_shape(self, shape):
        self.space.add(shape)
        self.shapes.append(shape)

    def add_constraint(self, constraint):
        self.space.add(constraint)
        self.constraints.append(constraint)

    def remove_body(self, body):
        if body in self.bodies:
            self.space.remove(body)
            self.bodies.remove(body)

    def remove_shape(self, shape):
        if shape in self.shapes:
            self.space.remove(shape)
            self.shapes.remove(shape)
        self._contacting_pairs = {(s1, s2) for s1, s2 in self._contacting_pairs
                                   if s1 is not shape and s2 is not shape}

    def remove_constraint(self, constraint):
        if constraint in self.constraints:
            self.space.remove(constraint)
            self.constraints.remove(constraint)

    def step(self, dt):
        self.space.step(dt)

    def clear(self):
        for c in self.constraints[:]:
            self.space.remove(c)
        for s in self.shapes[:]:
            self.space.remove(s)
        for b in self.bodies[:]:
            self.space.remove(b)
        self.constraints.clear()
        self.shapes.clear()
        self.bodies.clear()
        self._contacting_pairs.clear()
