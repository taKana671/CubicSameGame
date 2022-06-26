import itertools
import random
import sys
from enum import Enum, auto

from direct.particles.ParticleEffect import ParticleEffect


from direct.interval.IntervalGlobal import Sequence, Parallel, Func, Wait
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

SIZE = 4

TURN_UP = 'TurnUp'
TURN_DOWN = 'TurnDown'
TURN_RIGHT = 'TurnRight'
TURN_LEFT = 'TurnLeft'


class Status(Enum):

    PLAY = auto()
    CLICKED = auto()
    DELETE = auto()
    MOVE = auto()


class Colors(Enum):

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
        return random.sample([m.value for m in cls], n)


class Sphere:

    def __init__(self, node_path, point, tag, color, pos):
        """color: LColor
           pos: Vec3
        """
        self.tag = tag
        self.color = color
        self.pos = pos
        self.point = point
        self.destination = False

        self.model = base.loader.loadModel(PATH_SPHERE)
        self.model.reparentTo(node_path)
        self.model.setScale(0.2)
        self.model.setColor(self.color)
        self.model.setPos(self.pos)

        self.model.find('**/Sphere').node().setIntoCollideMask(BitMask32.bit(1))
        self.model.find('**/Sphere').node().setTag('sphere', str(self.tag))
        # render/sphereRoot/sphere.egg/Sphere

    @property
    def distance(self):
        return (self.pos.x ** 2 + self.pos.y ** 2 + self.pos.z ** 2) ** 0.5

    def rotate_around(self, angle, axis):
        q = Quat()
        q.setFromAxisAngle(angle, axis.normalized())
        r = q.xform(self.pos - self.point)
        self.pos = self.point + r

        if self.model:
            self.model.setPos(self.pos)

        # object_pos = self.model.getPos()
        # q = Quat()
        # q.setFromAxisAngle(angle, axis.normalized())
        # r = q.xform(object_pos - point)
        # rotated_pos = point + r
        # self.model.setPos(rotated_pos)

    def shake(self):
        return Sequence(
            self.model.posInterval(0.1, self.pos + (0, 0, 0.2)),
            self.model.posInterval(0.1, self.pos - (0, 0, 0.2)),
            self.model.posInterval(0.1, self.pos),
        )

    def _delete(self):
        self.model.removeNode()
        self.model = None
        self.color = None

    def disappear(self):
        return Sequence(
            self.model.scaleInterval(0.3, 0.01),
            Func(self._delete)
        )

    def set_destination(self, cell):
        self.destination = False
        cell.destination = True
        cell.model = self.model
        cell.color = self.color
        self.model, self.color = None, None

    def move_model(self):
        return Sequence(
            self.model.posInterval(0.2, self.pos),
            Func(lambda: self.model.find('**/Sphere').node().setTag('sphere', str(self.tag)))
        )


class Game(ShowBase):

    def __init__(self):
        super().__init__()
        self.disableMouse()
        self.camera.setPos(20, -20, 15)
        self.camera.lookAt(0, 0, 0)
        self.status = Status.PLAY
        self.sphere_moving = None
        self.deleted = False

        self.wind = Window('CubicSameGame')
        self.ambient_light = BasicAmbientLight()
        self.directional_light = BasicDayLight()

        self.setup_controls()
        self.setup_collision_detection()

        self.colors = Colors.select(4)
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

        for i, (x, y, z) in enumerate(itertools.product(range(4), repeat=3)):
            idx = random.randint(0, 3)
            pos = Vec3(pts[x], pts[y], pts[z])
            sphere = Sphere(
                self.sphere_root, point, i, self.colors[idx], pos
            )
            self.spheres[x][y][z] = sphere

        # for i in range(64):
        #     x, y, z = self.get_components(i)
        #     idx = random.randint(0, 3)
        #     print(pts[x], pts[y], pts[z])
        #     pos = Vec3(pts[x], pts[y], pts[z])
        #     sphere = Sphere(
        #         self.sphere_root, point, i, self.colors[idx], pos)
        #     self.spheres[x][y][z] = sphere

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

            if self.handler.getNumEntries() > 0:
                self.handler.sortEntries()
                tag = int(self.handler.getEntry(0).getIntoNode().getTag('sphere'))
                # print([s.getIntoNode().getTag('sphere') for s in self.handler.getEntries()])
                print(tag)
                self.delete(tag)

    def delete(self, tag):
        x, y, z = self.get_components(tag)
        sphere = self.spheres[x][y][z]
        self.sequence = Sequence(sphere.shake())

        if self.is_deletable(x, y, z, sphere.color):
            para = Parallel(sphere.disappear())
            for x, y, z in self.find_same_colors(x, y, z, sphere.color):
                para.append(self.spheres[x][y][z].disappear())
            self.sequence.append(para)
        self.sequence.start()

        if len(self.sequence.ivals) == 1:
            self.status = Status.CLICKED
        else:
            self.status = Status.DELETE

    def update(self, task):
        if self.status == Status.PLAY:
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
                for x, y, z in itertools.product(range(SIZE), repeat=3):
                    sphere = self.spheres[x][y][z]
                    sphere.rotate_around(rotation_angle, axis)

        if self.status == Status.CLICKED:
            if not self.sequence.isPlaying():
                self.status = Status.PLAY

        if self.status == Status.DELETE:
            if not self.sequence.isPlaying():
                self.status = Status.MOVE

        if self.status == Status.MOVE:
            if not self.sphere_moving:
                if not self.move():
                    self.status = Status.PLAY
            else:
                if not self.sphere_moving.isPlaying():
                    self.sphere_moving = None

        return task.cont

    def _find(self, x, y, z, color, dx=0, dy=0, dz=0):
        x, y, z = x + dx, y + dy, z + dz
        if not ((0 <= x < 4) and (0 <= y < 4) and (0 <= z < 4)):
            return
        if self.spheres[x][y][z].color != color:
            return
        yield (x, y, z)
        yield from self._find(x, y, z, color, dx, dy, dz)

    def find_same_colors(self, x, y, z, color):
        yield from self._find(x, y, z, color, dx=1)
        yield from self._find(x, y, z, color, dx=-1)
        yield from self._find(x, y, z, color, dy=1)
        yield from self._find(x, y, z, color, dy=-1)
        yield from self._find(x, y, z, color, dz=1)
        yield from self._find(x, y, z, color, dz=-1)

    def get_neighbors(self, x, y, z):
        for nx, ny, nz in [(x + 1, y, z), (x - 1, y, z), (x, y + 1, z),
                           (x, y - 1, z), (x, y, z + 1), (x, y, z - 1)]:
            if 0 <= nx < SIZE and 0 <= ny < SIZE and 0 <= nz < SIZE:
                yield nx, ny, nz

    def is_deletable(self, x, y, z, color):
        for nx, ny, nz in self.get_neighbors(x, y, z):
            if self.spheres[nx][ny][nz].color == color:
                return True
        return False

        # if x + 1 < SIZE and self.spheres[x + 1][y][z].color == color:
        #     return True
        # if x - 1 >= 0 and self.spheres[x - 1][y][z].color == color:
        #     return True
        # if y + 1 < SIZE and self.spheres[x][y + 1][z].color == color:
        #     return True
        # if y - 1 >= 0 and self.spheres[x][y - 1][z].color == color:
        #     return True
        # if z + 1 < SIZE and self.spheres[x][y][z + 1].color == color:
        #     return True
        # if z - 1 >= 0 and self.spheres[x][y][z - 1].color == color:
        #     return True

        # return False

    def move(self):
        if destinations := [cell for cell in self.set_destinations()]:
            # print([(d.tag, d.destination) for d in destinations])
            self.sphere_moving = Parallel()
            for cell in destinations:
                if cell.destination:
                    self.sphere_moving.append(cell.move_model())
            self.sphere_moving.start()
            return True
        return False

    def set_destinations(self):
        search = True
        while search:
            search = False
            for x, y, z in itertools.product(range(SIZE), repeat=3):
                if (sphere := self.spheres[x][y][z]).color:
                    if empty_cells := [c for c in self.empty_cells(x, y, z)]:
                        empty_cell = min(empty_cells, key=lambda x: x.distance)
                        if empty_cell.distance < sphere.distance:
                            sphere.set_destination(empty_cell)
                            yield empty_cell
                            search = True
                            break

    def empty_cells(self, x, y, z):
        for nx, ny, nz in self.get_neighbors(x, y, z):
            if not self.spheres[nx][ny][nz].color:
                yield self.spheres[nx][ny][nz]


    # def check_colors(self, i):
    #     # x * 16 + y * 4 + z
    #     x, y, z = self.get_components(i)


game = Game()
game.run()