import pyglet as pgl
from Node import Node


class Inverter(Node):
    def __init__(self, x, y, view_x, view_y, scale, batch=None):
        super().__init__(x, y, view_x, view_y, scale, batch = batch)
        self.image = pgl.image.load('resources/inverter.png')
        self.powered = True

        self._power_overlay = pgl.sprite.Sprite(pgl.image.load('resources/inverter_power.png'), view_x, view_y,
                                                batch=batch, group=pgl.graphics.OrderedGroup(2))
        self._power_overlay.opacity = 255
        self._power_overlay.scale = scale

        self._selected_overlay = pgl.sprite.Sprite(pgl.image.load('resources/inverter_select.png'), view_x, view_y,
                                                   batch=batch)
        self._selected_overlay.opacity = 0
        self._selected_overlay.scale = scale

    def update_power(self):
        """ Update powered state by checking all sources to see if they are powered,
        if any are, then powered is false, otherwise true """
        self.powered = True
        if any([source.powered for source in self.sources]): self.powered = False

        for child in self.children: child.update()
