import random
import sys
from enum import Enum

from direct.showbase.InputStateGlobal import inputState
from direct.showbase.ShowBaseGlobal import globalClock
from direct.showbase.ShowBase import ShowBase
from panda3d.core import NodePath, PandaNode, Quat, Vec3, LColor

from window import Window
from sphere import Sphere
from lights import BasicAmbientLight, BasicDayLight


TURN_UP = 'TurnUp'
TURN_DOWN = 'TurnDown'
TURN_RIGHT = 'TurnRight'
TURN_LEFT = 'TurnLeft'


class Color(Enum):

    RED = LColor(1, 0, 0, 1)
    BLUE = LColor(0, 1, 0, 1)
    YELLOW = LColor(1, 1, 0, 1)
    GREEN = LColor(0, 0.5, 0, 1)
    ORANGE = LColor(1, 0.549, 0, 1)
    MAGENTA = LColor(1, 0, 1, 1)
    PURPLE = LColor(0.501, 0, 0.501, 1)
    LIME = LColor(0, 1, 0, 1)

    @classmethod
    def select(cls, n):
        return random.sample(list(map(lambda c: c.value, cls)), n)


class Game(ShowBase):

    def __init__(self):
        super().__init__()
        self.setBackgroundColor(1, 1, 1)
        self.disableMouse()
        self.camera.setPos(20, -20, 15)
        self.camera.lookAt(0, 0, 0)

        # self.camera.setPos(20, -30, 5)
        # self.camera.lookAt(0, 20, 5)

        self.wind = Window('CubicSameGame')
        self.ambient_light = BasicAmbientLight()
        self.directional_light = BasicDayLight()

        self.create_key_controls()

        self.base_point = Vec3(0, 0, 0)
        self.colors = Color.select(4)
        self.spheres = [[[None for _ in range(4)] for _ in range(4)] for _ in range(4)]
        self.pos = [-3, -1, 1, 3]
        self.create_spheres()

        self.taskMgr.add(self.update, 'update')

    def create_key_controls(self):
        self.accept("escape", sys.exit)
        inputState.watchWithModifiers(TURN_UP, 'arrow_up')
        inputState.watchWithModifiers(TURN_DOWN, 'arrow_down')
        inputState.watchWithModifiers(TURN_LEFT, 'arrow_left')
        inputState.watchWithModifiers(TURN_RIGHT, 'arrow_right')

    def create_spheres(self):
        for x in range(4):
            for y in range(4):
                for z in range(4):
                    idx = random.randint(0, 3)
                    pos = Vec3(self.pos[x], self.pos[y], self.pos[z])
                    sphere = Sphere(self.colors[idx], pos)
                    self.spheres[x][y][z] = sphere

    def update(self, task):
        dt = globalClock.getDt()
        velocity = 0
        axis = Vec3.forward()

        if inputState.isSet(TURN_UP):
            velocity += 10
        elif inputState.isSet(TURN_DOWN):
            velocity -= 10
        elif inputState.isSet(TURN_LEFT):
            velocity += 10
            axis = Vec3.up()
        elif inputState.isSet(TURN_RIGHT):
            velocity -= 10
            axis = Vec3.up()

        rotation_angle = velocity * dt

        for x in range(4):
            for y in range(4):
                for z in range(4):
                    if sphere := self.spheres[x][y][z]:
                        sphere.rotate_around(rotation_angle, axis, self.base_point)

        return task.cont


game = Game()
game.run()