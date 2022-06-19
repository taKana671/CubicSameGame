import random
import sys
from enum import Enum

from direct.showbase.InputStateGlobal import inputState
from direct.showbase.ShowBaseGlobal import globalClock
from direct.showbase.ShowBase import ShowBase
from panda3d.core import NodePath, PandaNode, Quat, Vec3, LColor, BitMask32
from panda3d.core import CollisionTraverser, CollisionNode
from panda3d.core import CollisionHandlerQueue, CollisionRay

from window import Window
from lights import BasicAmbientLight, BasicDayLight


PATH_SPHERE = 'models/alice-shapes--sphere/sphere'


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


class Sphere:

    def __init__(self, node_path, tag, color, pos):
        """color: LColor
           pos: Vec3
        """
        self.model = base.loader.loadModel(PATH_SPHERE)
        self.model.reparentTo(node_path)
        self.model.setScale(0.2)
        self.model.setColor(color)
        self.model.setPos(pos)

        self.model.find('**/Sphere').node().setIntoCollideMask(BitMask32.bit(1))
        self.model.find('**/Sphere').node().setTag('sphere', str(tag))
        # render/squareRoot/square.egg/polygon

    def rotate_around(self, angle, axis, point):
        object_pos = self.model.getPos()
        q = Quat()
        q.setFromAxisAngle(angle, axis.normalized())
        r = q.xform(object_pos - point)
        rotated_pos = point + r
        self.model.setPos(rotated_pos)


class Game(ShowBase):

    def __init__(self):
        super().__init__()
        self.disableMouse()
        self.camera.setPos(20, -20, 15)
        self.camera.lookAt(0, 0, 0)

        self.wind = Window('CubicSameGame')
        self.ambient_light = BasicAmbientLight()
        self.directional_light = BasicDayLight()

        self.setup_controls()
        self.setup_collision_detection()

        self.base_point = Vec3(0, 0, 0)
        self.colors = Color.select(4)
        self.spheres = [[[None for _ in range(4)] for _ in range(4)] for _ in range(4)]
        self.pos = [-3, -1, 1, 3]
        self.setup_spheres()

        self.taskMgr.add(self.update, 'update')

    def setup_collision_detection(self):
        self.picker = CollisionTraverser()
        self.handler = CollisionHandlerQueue()

        self.picker_node = CollisionNode('mouseRay')
        self.picker_np = self.camera.attachNewNode(self.picker_node)
        self.picker_node.setFromCollideMask(BitMask32.bit(1))
        self.picker_ray = CollisionRay()
        self.picker_node.addSolid(self.picker_ray)
        self.picker.addCollider(self.picker_np, self.handler)

    def setup_controls(self):
        self.accept('mouse1', self.click)
        self.accept("escape", sys.exit)
        inputState.watchWithModifiers(TURN_UP, 'arrow_up')
        inputState.watchWithModifiers(TURN_DOWN, 'arrow_down')
        inputState.watchWithModifiers(TURN_LEFT, 'arrow_left')
        inputState.watchWithModifiers(TURN_RIGHT, 'arrow_right')

    def setup_spheres(self):
        self.sphere_root = self.render.attachNewNode('sphereRoot')
        i = 0

        for x in range(4):
            for y in range(4):
                for z in range(4):
                    idx = random.randint(0, 3)
                    pos = Vec3(self.pos[x], self.pos[y], self.pos[z])
                    sphere = Sphere(self.sphere_root, i, self.colors[idx], pos)
                    self.spheres[x][y][z] = sphere
                    i += 1

    def click(self):
        if self.mouseWatcherNode.hasMouse():
            pos = self.mouseWatcherNode.getMouse()
            self.picker_ray.setFromLens(self.camNode, pos.getX(), pos.getY())

            self.picker.traverse(self.sphere_root)
            # import pdb; pdb.set_trace()
            if self.handler.getNumEntries() > 0:
                self.handler.sortEntries()
                idx = int(self.handler.getEntry(0).getIntoNode().getTag('sphere'))
                print(idx)

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