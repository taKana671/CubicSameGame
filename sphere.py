from panda3d.core import NodePath, PandaNode, LColor, Quat


PATH_SPHERE = 'models/alice-shapes--sphere/sphere'

RED = LColor(1, 0, 0, 1)


class Sphere(NodePath):

    def __init__(self):
        super().__init__(PandaNode("Sphere"))
        self.reparentTo(base.render)
        model = base.loader.loadModel(PATH_SPHERE)
        model.setName("sphereModel")
        model.reparentTo(self)
        self.setScale(0.2)
        self.setColor(RED)
        # self.setPos(-5, 0, 0)

    def rotate_around(self, angle, axis, point):
        object_pos = self.getPos()
        q = Quat()
        q.setFromAxisAngle(angle, axis.normalized())
        r = q.xform(object_pos - point)
        rotated_pos = point + r
        self.setPos(rotated_pos)