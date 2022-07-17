from direct.interval.IntervalGlobal import Sequence, Func
from direct.showbase.ShowBase import ShowBase
from panda3d.core import PandaNode, NodePath, Quat
from panda3d.core import Vec3, Point3


PATH_SPACE = 'models/space/solar_sky_sphere'
PATH_SPACE_TEXTURE = 'models/space/stars_1k_tex.jpg'
PATH_PLANETS = 'models/planets/planet_sphere'
PATH_EARTH_TEXTURE = 'models/planets/earth_1k_tex.jpg'
PATH_MOON_TEXTURE = 'models/planets/moon_1k_tex.jpg'
PATH_SATELLITE_TEXTURE = 'models/planets/phobos_1k_tex.jpg'
PATH_SUN_TEXTURE = 'models/planets/sun_1k_tex.jpg'


class CosmicSpace(NodePath):

    def __init__(self):
        super().__init__(PandaNode('cosmicSpace'))
        self.reparentTo(base.render)
        space = base.loader.loadModel(PATH_SPACE)
        space.setScale(40)
        tex = base.loader.loadTexture(PATH_SPACE_TEXTURE)
        space.setTexture(tex, 1)
        space.reparentTo(self)


class Earth(NodePath):

    def __init__(self):
        super().__init__(PandaNode('earth'))
        self.reparentTo(base.render)
        earth = base.loader.loadModel(PATH_PLANETS)
        earth.setTexture(base.loader.loadTexture(PATH_EARTH_TEXTURE), 1)
        earth.setScale(15)
        earth.setPos(Point3(-30, 10, -20))
        earth.reparentTo(self)
        earth.hprInterval(120, Vec3(0, 360, 0)).loop()


class Moon(NodePath):
    def __init__(self):
        super().__init__(PandaNode('moon'))
        self.reparentTo(base.render)
        center = Point3(-5, 30, 2)
        moon = base.loader.loadModel(PATH_PLANETS)
        moon.setTexture(base.loader.loadTexture(PATH_MOON_TEXTURE), 1)
        moon.setScale(5)
        moon.setPos(center)
        moon.reparentTo(self)
        moon.hprInterval(120, Vec3(0, 360, 0)).loop()
        self.sattelite = Satellite(center, Vec3.right(), 30)


class Satellite(NodePath):

    def __init__(self, center, axis, velocity):
        super().__init__(PandaNode('satellite'))
        self.reparentTo(base.render)
        self.satellite = base.loader.loadModel(PATH_PLANETS)
        self.satellite.setTexture(
            base.loader.loadTexture(PATH_SATELLITE_TEXTURE), 1)
        self.satellite.setScale(0.3)
        self.point = center
        self.axis = axis
        self.angular_velocity = velocity
        self.satellite.setPos(Point3(-6, 20, 3))
        self.satellite.reparentTo(self)

    def rotate_around(self, time):
        rotation_angle = self.angular_velocity * time
        object_pos = self.satellite.getPos()
        q = Quat()
        q.setFromAxisAngle(rotation_angle, self.axis.normalized())
        r = q.xform(object_pos - self.point)
        rotated_pos = self.point + r
        self.satellite.setPos(rotated_pos)

        forward = self.axis.cross(r)
        if rotation_angle < 0:
            forward *= -1
        self.satellite.lookAt(rotated_pos + forward, self.axis)


class Sun(NodePath):

    def __init__(self):
        super().__init__(PandaNode('sun'))
        self.reparentTo(base.render)
        self.sun = base.loader.loadModel(PATH_PLANETS)
        self.sun.setTexture(base.loader.loadTexture(PATH_SUN_TEXTURE), 1)
        self.sun.setScale(0.3)
        self.sun.setPos(Point3(0, 5, 10))
        self.seq = Sequence(
            self.hprInterval(5, Vec3(0, 360, 0)),
            Func(lambda: self.sun.detachNode()),
        )

    def rotate_around(self):
        if not self.seq.isPlaying():
            self.sun.reparentTo(self)
            self.seq.start()


class Scene:

    def __init__(self):
        self.space = CosmicSpace()
        self.moon = Moon()
        self.earth = Earth()
        self.sun = Sun()


if __name__ == '__main__':
    base = ShowBase()
    base.setBackgroundColor(0, 0, 0)
    base.disableMouse()
    base.camera.setPos(20, -20, 5)
    base.camera.lookAt(0, 0, 0)
    scene = Scene()
    base.run()
