from panda3d.core import AmbientLight, DirectionalLight
from panda3d.core import Point3, Vec3, LColor, NodePath


class BasicAmbientLight(NodePath):

    def __init__(self):
        super().__init__(AmbientLight('BasicAmbientLight'))
        self.reparentTo(base.render)
        self.node().setColor(LColor(0.6, 0.6, 0.6, 1))
        base.render.setLight(self)


class BasicDayLight(NodePath):

    def __init__(self):
        super().__init__(DirectionalLight('basicDayLight'))
        self.reparentTo(base.render)
        self.node().getLens().setFilmSize(200, 200)
        self.node().getLens().setNearFar(1, 100)
        self.node().setColor(LColor(1, 1, 1, 1))
        self.setPosHpr(Point3(0, 0, 50), Vec3(-30, -45, 0))
        base.render.setLight(self)

        self.node().setShadowCaster(True)
        base.render.setShaderAuto()