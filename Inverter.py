import pyglet as pgl
from Node import Node


class Inverter(Node):
    def __init__(self, x, y, view_x, view_y, scale, batch=None):
        super().__init__(x, y, view_x, view_y, scale, batch = batch)
        self.image = pgl.image.load('resources/inverter.png')

        self._selected_overlay.image = pgl.image.load('resources/inverter_select.png')
        self._power_overlay.image = pgl.image.load('resources/inverter_power.png')
        self._power_overlay.visible = True

        self.powered = True
        self._center_image()

    def update_power(self):
        """ Update powered state by checking all sources to see if they are powered,
        if any are, then powered is false, otherwise true """
        prev_power = self.powered

        self.powered = True
        if any([source.powered for source in self.sources]): self.powered = False

        # preform updates only if power state has changed
        if self.powered != prev_power:
            if self.powered:
                self._power_overlay.visible = True
            else:
                self._power_overlay.visible = False

            for child in self.children:
                child.update()
