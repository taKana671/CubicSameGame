import itertools
import random
import sys
from enum import Enum, auto

from direct.gui.DirectGui import OnscreenText, ScreenTitle
from direct.interval.IntervalGlobal import Sequence, Parallel, Func, Wait
from direct.showbase.InputStateGlobal import inputState
from direct.showbase.ShowBaseGlobal import globalClock
from direct.showbase.ShowBase import ShowBase
from panda3d.core import TextNode
from panda3d.core import Quat, Vec3, LColor, BitMask32
from panda3d.core import CollisionTraverser, CollisionNode
from panda3d.core import CollisionHandlerQueue, CollisionRay

from window import Window
from lights import BasicAmbientLight, BasicDayLight
# from panda3d.core import AmbientLight, DirectionalLight


PATH_SPHERE = 'models/alice-shapes--sphere/sphere'
SIZE = 4


class Arrow(Enum):
    UP = 'arrow_down'
    DOWN = 'arrow_up'
    RIGHT = 'arrow_left'
    LEFT = 'arrow_right'

    @property
    def key(self):
        return self.name

    @classmethod
    def keys(cls):
        return [(c.name, c.value) for c in cls]


class Status(Enum):

    PLAY = auto()
    CLICKED = auto()
    DELETE = auto()
    MOVE = auto()
    JUDGE = auto()
    GAMEOVER = auto()


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
        self.score = 0

        self.wind = Window('CubicSameGame')
        self.ambient_light = BasicAmbientLight()
        self.directional_light = BasicDayLight()
        # self.setup_lights()

        self.setup_texts()
        self.setup_controls()
        self.setup_collision_detection()

        self.sphere_root = self.render.attachNewNode('sphereRoot')
        self.setup_spheres()

        self.taskMgr.add(self.update, 'update')

    def setup_texts(self):
        self.score_text = 'Score: {}'
        self.score_dislay = OnscreenText(
            parent=self.a2dBottomRight,
            text=self.score_text.format(self.score),
            style=ScreenTitle,
            fg=(1, 1, 1, 1),
            pos=(-0.1, 0.09),
            align=TextNode.ARight,
            scale=0.07,
            mayChange=True
        )
        instructions = OnscreenText(
            parent=self.a2dTopLeft,
            style=ScreenTitle,
            fg=(1, 1, 1, 1),
            pos=(0.06, -0.1),
            align=TextNode.ALeft,
            scale=0.05
        )
        instructions.appendText('Esc: Quit\r\n')
        instructions.appendText('Left-click: Select to delete\r\n')
        instructions.appendText('Arrows: Rotate\r\n')

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

        for name, key in Arrow.keys():
            inputState.watchWithModifiers(name, key)

    def setup_spheres(self):
        pts = [-3, -1, 1, 3]
        point = Vec3(0, 0, 0)
        self.colors = Colors.select(4)
        self.spheres = [[[None for _ in range(4)] for _ in range(4)] for _ in range(4)]

        for i, (x, y, z) in enumerate(itertools.product(range(4), repeat=3)):
            idx = random.randint(0, 3)
            pos = Vec3(pts[x], pts[y], pts[z])
            sphere = Sphere(
                self.sphere_root, point, i, self.colors[idx], pos
            )
            self.spheres[x][y][z] = sphere

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

    def get_components(self, tag):
        x = tag // 16
        y = (tag // 4) % 4
        z = tag % 4
        return x, y, z

    def show_score(self, cnt=0):
        self.score += cnt
        self.score_dislay.setText(self.score_text.format(self.score))

    def delete(self, tag):
        x, y, z = self.get_components(tag)
        self.sequence = Sequence(self.spheres[x][y][z].shake())
        self.status = Status.CLICKED

        if same_spheres := [s.disappear() for s in self.find_same_colors(x, y, z)]:
            disappear = Parallel(*same_spheres)
            self.show_score(len(disappear))
            self.sequence.append(disappear)
            self.status = Status.DELETE

        self.sequence.start()

    def update(self, task):
        if self.status == Status.PLAY:
            dt = globalClock.getDt()
            velocity = 0
            axis = Vec3.forward()

            if inputState.isSet(Arrow.UP.key):
                velocity += 10
            elif inputState.isSet(Arrow.DOWN.key):
                velocity -= 10
            elif inputState.isSet(Arrow.LEFT.key):
                velocity += 10
                axis = Vec3.up()
            elif inputState.isSet(Arrow.RIGHT.key):
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
                    if self.is_gameover():
                        self.status = Status.GAMEOVER
                    else:
                        self.status = Status.PLAY
            else:
                if not self.sphere_moving.isPlaying():
                    self.sphere_moving = None

        if self.status == Status.GAMEOVER:
            if not self.gameover_seq.isPlaying():
                self.status = Status.PLAY

        return task.cont

    def _find(self, x, y, z, color, dx=0, dy=0, dz=0):
        x, y, z = x + dx, y + dy, z + dz
        if not ((0 <= x < 4) and (0 <= y < 4) and (0 <= z < 4)):
            return
        if self.spheres[x][y][z].color != color:
            return

        yield self.spheres[x][y][z]
        yield from self._find(x, y, z, color, dx, dy, dz)

    def find_same_colors(self, x, y, z):
        if self.is_deletable(x, y, z):
            sphere = self.spheres[x][y][z]
            yield sphere
            yield from self._find(x, y, z, sphere.color, dx=1)
            yield from self._find(x, y, z, sphere.color, dx=-1)
            yield from self._find(x, y, z, sphere.color, dy=1)
            yield from self._find(x, y, z, sphere.color, dy=-1)
            yield from self._find(x, y, z, sphere.color, dz=1)
            yield from self._find(x, y, z, sphere.color, dz=-1)

    def get_neighbors(self, x, y, z):
        for nx, ny, nz in [(x + 1, y, z), (x - 1, y, z), (x, y + 1, z),
                           (x, y - 1, z), (x, y, z + 1), (x, y, z - 1)]:
            if 0 <= nx < SIZE and 0 <= ny < SIZE and 0 <= nz < SIZE:
                yield nx, ny, nz

    def is_deletable(self, x, y, z):
        for nx, ny, nz in self.get_neighbors(x, y, z):
            if self.spheres[nx][ny][nz].color == self.spheres[x][y][z].color:
                return True
        return False

    def move(self):
        if destinations := [cell for cell in self.set_destinations()]:
            self.sphere_moving = Parallel(
                *[c.move_model() for c in destinations if c.destination])
            self.sphere_moving.start()
            return True
        return False

    def set_destinations(self):
        for x, y, z in itertools.product(range(SIZE), repeat=3):
            if (sphere := self.spheres[x][y][z]).color:
                if empty_cells := [c for c in self.empty_cells(x, y, z)]:
                    empty_cell = min(empty_cells, key=lambda x: x.distance)
                    if empty_cell.distance < sphere.distance:
                        sphere.set_destination(empty_cell)
                        yield empty_cell
                        yield from self.set_destinations()
                        break

    def empty_cells(self, x, y, z):
        for nx, ny, nz in self.get_neighbors(x, y, z):
            if not self.spheres[nx][ny][nz].color:
                yield self.spheres[nx][ny][nz]

    def _initialize(self):
        self.sphere_moving = None
        self.score = 0
        self.show_score()
        self.setup_spheres()

    def is_gameover(self):
        if self.can_continue():
            return False

        msg = OnscreenText(
            parent=self.aspect2d,
            text='You Won!' if self.score == 64 else 'Game Over',
            style=ScreenTitle,
            fg=(1, 1, 1, 1),
            pos=(0, 0),
            align=TextNode.ACenter,
            scale=0.2
        )
        self.gameover_seq = Sequence(
            Wait(1),
            msg.scaleInterval(0.5, 0.01),
            Func(lambda: msg.destroy()),
            Wait(0.5)
        )
        if left_spheres := [s.disappear() for x, y, z in itertools.product(range(SIZE), repeat=3)
                            if (s := self.spheres[x][y][z]).color]:
            self.gameover_seq.extend([Parallel(*left_spheres), Wait(0.5)])

        self.gameover_seq.append(Func(self._initialize))
        self.gameover_seq.start()

        return True

    def can_continue(self):
        for x, y, z in itertools.product(range(SIZE), repeat=3):
            if self.spheres[x][y][z].color:
                if self.is_deletable(x, y, z):
                    return True
        return False


game = Game()
game.run()