import sys

from direct.showbase.InputStateGlobal import inputState
from direct.showbase.ShowBaseGlobal import globalClock
from direct.showbase.ShowBase import ShowBase
from panda3d.core import NodePath, PandaNode, Quat, Vec3

from window import Window
from sphere import Sphere
from lights import BasicAmbientLight, BasicDayLight


TURN_UP = 'TurnUp'
TURN_DOWN = 'TurnDown'
TURN_RIGHT = 'TurnRight'
TURN_LEFT = 'TurnLeft'


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
        self.taskMgr.add(self.update, 'update')

        self.spheres = [s for s in self.create_spheres()]

        # self.root = self.render.attachNewNode('Spheres')

        # sphere1 = Sphere()
        # sphere1.setPos(-5, 0, 0)
        # sphere2 = Sphere()
        # sphere2.setPos(-3, 0, 0)
        # sphere3 = Sphere()
        # sphere3.setPos(-5, 0, -2)

        # self.spheres = [sphere1, sphere2, sphere3]

        # sphere.setScale(0.2)
        # sphere.setColor(RED)
        # sphere.setPos(-5, 0, 0)

    def create_key_controls(self):
        self.accept("escape", sys.exit)
        inputState.watchWithModifiers(TURN_UP, 'arrow_up')
        inputState.watchWithModifiers(TURN_DOWN, 'arrow_down')
        inputState.watchWithModifiers(TURN_LEFT, 'arrow_left')
        inputState.watchWithModifiers(TURN_RIGHT, 'arrow_right')

    def create_spheres(self):
        for x in [-5, -2.5, 0, 2.5]:
            for y in [-5, -2.5, 0, 2.5]:
                for z in [-5, -2.5, 0, 2.5]:
                    sphere = Sphere()
                    sphere.setPos(x, y, z)
                    yield sphere

    def update(self, task):
        dt = globalClock.getDt()
        velocity = 0
        point = Vec3(0, 0, 0)
        axis = Vec3.forward()

        if inputState.isSet(TURN_UP):
            velocity += 10
        if inputState.isSet(TURN_DOWN):
            velocity -= 10
        if inputState.isSet(TURN_LEFT):
            velocity += 10
            axis = Vec3.up()
        if inputState.isSet(TURN_RIGHT):
            velocity -= 10
            axis = Vec3.up()

        # axis = Vec3.up()
        # print(velocity)
        rotation_angle = velocity * dt

        for s in self.spheres:
            s.rotate_around(rotation_angle, axis, point)

        return task.cont



game = Game()
game.run()