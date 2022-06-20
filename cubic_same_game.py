import random
import sys
from enum import Enum

from direct.particles.ParticleEffect import ParticleEffect


from direct.interval.IntervalGlobal import Sequence, ParticleInterval, Func, Wait
from direct.showbase.InputStateGlobal import inputState
from direct.showbase.ShowBaseGlobal import globalClock
from direct.showbase.ShowBase import ShowBase
from panda3d.core import NodePath, PandaNode, Quat, Vec3, LColor, BitMask32
from panda3d.core import CollisionTraverser, CollisionNode
from panda3d.core import CollisionHandlerQueue, CollisionRay

from window import Window
from lights import BasicAmbientLight, BasicDayLight


PATH_SPHERE = 'models/alice-shapes--sphere/sphere'
PATH_PARTICLES = 'disappear.ptf'


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

    def __init__(self, node_path, point, tag, color, pos):
        """color: LColor
           pos: Vec3
        """
        self.color = color
        self.model_pos = pos
        self.point = point

        self.node_path = node_path

        self.model = base.loader.loadModel(PATH_SPHERE)
        self.model.reparentTo(node_path)
        self.model.setScale(0.2)
        self.model.setColor(self.color)
        self.model.setPos(self.model_pos)

        self.model.find('**/Sphere').node().setIntoCollideMask(BitMask32.bit(1))
        self.model.find('**/Sphere').node().setTag('sphere', str(tag))
        # render/sphereRoot/sphere.egg/Sphere

    def rotate_around(self, angle, axis):
        q = Quat()
        q.setFromAxisAngle(angle, axis.normalized())
        r = q.xform(self.model_pos - self.point)
        self.model_pos = self.point + r

        if self.model:
            self.model.setPos(self.model_pos)

        # object_pos = self.model.getPos()
        # q = Quat()
        # q.setFromAxisAngle(angle, axis.normalized())
        # r = q.xform(object_pos - point)
        # rotated_pos = point + r
        # self.model.setPos(rotated_pos)

    def swing(self):
        Sequence(
            self.model.posInterval(0.1, self.model_pos + (0, 0, 0.2)),
            self.model.posInterval(0.1, self.model_pos - (0, 0, 0.2)),
            self.model.posInterval(0.1, self.model_pos),
            # self.model.scaleInterval(0.3, 0.01),
            Wait(0.5),
        ).start()


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

        self.colors = Color.select(4)
        self.sphere_root = self.render.attachNewNode('sphereRoot')
        self.spheres = [[[None for _ in range(4)] for _ in range(4)] for _ in range(4)]
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
        pts = [-3, -1, 1, 3]
        point = Vec3(0, 0, 0)

        for i in range(64):
            x, y, z = self.get_components(i)
            idx = random.randint(0, 3)
            pos = Vec3(pts[x], pts[y], pts[z])
            sphere = Sphere(
                self.sphere_root, point, i, self.colors[idx], pos)
            self.spheres[x][y][z] = sphere

        print(self.spheres)

    def get_components(self, i):
        x = i // 16
        y = (i // 4) % 4
        z = i % 4
        return x, y, z

    def click(self):
        if self.mouseWatcherNode.hasMouse():
            pos = self.mouseWatcherNode.getMouse()
            self.picker_ray.setFromLens(self.camNode, pos.getX(), pos.getY())

            self.picker.traverse(self.sphere_root)
            # import pdb; pdb.set_trace()
            if self.handler.getNumEntries() > 0:
                self.handler.sortEntries()
                i = int(self.handler.getEntry(0).getIntoNode().getTag('sphere'))
                print(i)
                # print([s.getIntoNode().getTag('sphere') for s in self.handler.getEntries()])
                self.spheres[i].swing()

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

        if rotation_angle := velocity * dt:
            for i in range(64):
                sphere = self.spheres[i]
                sphere.rotate_around(rotation_angle, axis)

        return task.cont

    def check_colors(self, i):
        # x * 16 + y * 4 + z
        x, y, z = self.get_components(i)
        


        


game = Game()
game.run()