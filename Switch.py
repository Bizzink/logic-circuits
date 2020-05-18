import pyglet as pgl
from Node import Node


class Switch(Node):
    def __init__(self, x, y, view_x, view_y, scale, batch=None):
        super().__init__(x, y, view_x, view_y, scale * 1.5, batch = batch)
        self.image = pgl.image.load('resources/switch_off.png')

        self._power_overlay = None
        self._selected_overlay.image = pgl.image.load('resources/switch_select.png')

        self._center_image()

    def flip(self):
        if self.powered:
            self.powered = False
            self.image = pgl.image.load('resources/switch_off.png')
        else:
            self.powered = True
            self.image = pgl.image.load('resources/switch_on.png')

        self._center_image()

        for child in self.children:
            child.update()

    def update_power(self, source = None):
        pass
