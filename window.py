from direct.showbase.ShowBase import ShowBase
from panda3d.core import WindowProperties


class Window:

    def __init__(self, title):
        self.props = WindowProperties()
        self.props.setTitle(title)
        self.props.setSize(800, 600)
        base.win.requestProperties(self.props)
        base.setBackgroundColor(0.5, 0.8, 1)


if __name__ == '__main__':
    base = ShowBase()
    wind = Window('sample')
    base.run()