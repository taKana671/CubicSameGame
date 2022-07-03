import itertools
import random
import sys
from enum import Enum, auto

from direct.gui.DirectGui import OnscreenText, ScreenTitle
from direct.gui.DirectGui import DirectOptionMenu, DirectLabel, DirectButton
from direct.interval.IntervalGlobal import Sequence, Parallel, Func, Wait
from direct.showbase.InputStateGlobal import inputState
from direct.showbase.ShowBaseGlobal import globalClock
from direct.showbase.ShowBase import ShowBase
from panda3d.core import TextNode
from panda3d.core import Quat, Vec3, LColor, BitMask32, Point3
from panda3d.core import AmbientLight, DirectionalLight
from panda3d.core import CollisionTraverser, CollisionNode
from panda3d.core import CollisionHandlerQueue, CollisionRay
from panda3d.core import WindowProperties


PATH_SPHERE = 'models/alice-shapes--sphere/sphere'


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
    GAMEOVER = auto()
    RESTART = auto()


class Colors(Enum):

    RED = LColor(1, 0, 0, 1)
    BLUE = LColor(0, 0, 1, 1)
    YELLOW = LColor(1, 1, 0, 1)
    GREEN = LColor(0, 0.5, 0, 1)
    ORANGE = LColor(1, 0.549, 0, 1)
    MAGENTA = LColor(1, 0, 1, 1)
    PURPLE = LColor(0.501, 0, 0.501, 1)
    LIME = LColor(0, 1, 0, 1)
    VIOLET = LColor(0.54, 0.16, 0.88, 1)
    SKY = LColor(0, 0.74, 1, 1)

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
        self.options = ['3', '4', '5', '6']
        self.size = self.next_size = 4

        self.setup_window()
        self.setup_lights()
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

    def setup_window(self):
        props = WindowProperties()
        props.setTitle('CubicSameGame')
        props.setSize(800, 600)
        self.win.requestProperties(props)
        self.setBackgroundColor(0.1, 0.1, 0.1)

    def setup_lights(self):
        ambient_light = self.render.attachNewNode(AmbientLight('ambientLight'))
        ambient_light.node().setColor(LColor(0.6, 0.6, 0.6, 1))
        self.render.setLight(ambient_light)

        directional_light = self.render.attachNewNode(DirectionalLight('directionalLight'))
        directional_light.node().getLens().setFilmSize(200, 200)
        directional_light.node().getLens().setNearFar(1, 100)
        directional_light.node().setColor(LColor(1, 1, 1, 1))
        directional_light.setPosHpr(Point3(0, 0, 30), Vec3(-30, -45, 0))
        directional_light.node().setShadowCaster(True)
        self.render.setShaderAuto()
        self.render.setLight(directional_light)

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
        start = self.size // 2 * -2 + 1 if self.size % 2 == 0 else self.size // 2 * -2
        pts = [start + i * 2 for i in range(self.size)]
        # pts = [-3, -1, 1, 3]
        point = Vec3(0, 0, 0)
        self.colors = Colors.select(self.size)
        self.spheres = [[[None for _ in range(self.size)] for _ in range(self.size)] for _ in range(self.size)]
        upper = self.size - 1

        for i, (x, y, z) in enumerate(itertools.product(range(self.size), repeat=3)):
            idx = random.randint(0, upper)
            pos = Vec3(pts[x], pts[y], pts[z])
            sphere = Sphere(
                self.sphere_root, point, i, self.colors[idx], pos
            )
            self.spheres[x][y][z] = sphere

    def click(self):
        if self.mouseWatcherNode.hasMouse() and self.status == Status.PLAY:
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
        x = tag // self.size ** 2
        y = (tag // self.size) % self.size
        z = tag % self.size
        return x, y, z

    def show_score(self, cnt=0):
        self.score += cnt
        self.score_dislay.setText(self.score_text.format(self.score))

    def delete(self, tag):
        x, y, z = self.get_components(tag)
        self.delete_seq = Sequence(self.spheres[x][y][z].shake())
        self.status = Status.CLICKED

        if same_spheres := [s.disappear() for s in self.find_same_colors(x, y, z)]:
            disappear = Parallel(*same_spheres)
            self.show_score(len(disappear))
            self.delete_seq.append(disappear)
            self.status = Status.DELETE

        self.delete_seq.start()

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
                for x, y, z in itertools.product(range(self.size), repeat=3):
                    sphere = self.spheres[x][y][z]
                    sphere.rotate_around(rotation_angle, axis)

        if self.status == Status.CLICKED:
            if not self.delete_seq.isPlaying():
                self.status = Status.PLAY
        elif self.status == Status.DELETE:
            if not self.delete_seq.isPlaying():
                self.status = Status.MOVE
        elif self.status == Status.MOVE:
            if not self.sphere_moving:
                if not self.move():
                    if self.can_continue():
                        self.status = Status.PLAY
                    else:
                        self.status = Status.GAMEOVER
                        self.show_gameover_screen()
            else:
                if not self.sphere_moving.isPlaying():
                    self.sphere_moving = None
        elif self.status == Status.RESTART:
            if not self.gameover_seq.isPlaying():
                self.status = Status.PLAY

        return task.cont

    def _find(self, x, y, z, color, dx=0, dy=0, dz=0):
        x, y, z = x + dx, y + dy, z + dz
        if not ((0 <= x < self.size) and (0 <= y < self.size) and (0 <= z < self.size)):
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
            if 0 <= nx < self.size and 0 <= ny < self.size and 0 <= nz < self.size:
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
        for x, y, z in itertools.product(range(self.size), repeat=3):
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
        self.size = self.next_size
        self.score = 0
        self.show_score()
        self.setup_spheres()

    def show_gameover_screen(self):
        gui_root = self.aspect2d.attachNewNode('guiRoot')

        OnscreenText(
            parent=gui_root,
            text='You Won!' if self.score == self.size ** 3 else 'Game Over',
            style=ScreenTitle,
            fg=(1, 1, 1, 1),
            pos=(0, 0.2),
            align=TextNode.ACenter,
            scale=0.2
        )
        DirectLabel(
            parent=gui_root,
            pos=(-0.1, 0, -0.2),
            text='Select Size',
            text_fg=(1, 1, 1, 1),
            frameColor=(1, 1, 1, 0),
            scale=0.08,
        )
        DirectOptionMenu(
            parent=gui_root,
            pos=(0.2, 0, -0.2),
            scale=0.1,
            items=self.options,
            initialitem=self.options.index(str(self.size)),
            highlightColor=(0.65, 0.65, 0.65, 1),
            command=self.change_size
        )
        DirectButton(
            parent=gui_root,
            pos=(0, 0, -0.5),
            scale=0.1,
            frameSize=(-2, 2, -0.8, 0.8),
            text='START',
            text_pos=(0, -0.3),
            command=lambda: self.restart_game(gui_root)
        )

    def restart_game(self, gui_root):
        self.gameover_seq = Sequence(
            Wait(0.3),
            Func(lambda: gui_root.removeNode()),
            Wait(0.5)
        )
        if left_spheres := [s.disappear() for x, y, z in itertools.product(range(self.size), repeat=3)
                            if (s := self.spheres[x][y][z]).color]:
            self.gameover_seq.extend([Parallel(*left_spheres), Wait(0.5)])

        self.gameover_seq.append(Func(self._initialize))
        self.gameover_seq.start()
        self.status = Status.RESTART

    def can_continue(self):
        for x, y, z in itertools.product(range(self.size), repeat=3):
            if self.spheres[x][y][z].color:
                if self.is_deletable(x, y, z):
                    return True
        return False

    def change_size(self, size):
        self.next_size = int(size)


game = Game()
game.run()