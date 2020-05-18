from math import atan2, pi
import pyglet as pgl


class _Child:
    """ Handles connections between nodes """

    def __init__(self, parent, child, batch):
        child.add_source(parent)
        child.update_power()

        self._child = child
        self._parent = parent
        self._line = None
        self._arrow = None
        self._deleted = False

        self._line = batch.add(2, pgl.gl.GL_LINES, None,
                               ('v2i', (parent.x, parent.y, child.x, child.y)),
                               ('c3B', (150, 150, 150, 150, 150, 150)))

        self._arrow = pgl.sprite.Sprite(pgl.image.load('resources/connection_direction.png'),
                                        x=parent.x + (child.x - parent.x) // 2,
                                        y=parent.y + (child.y - parent.y) // 2,
                                        batch=batch)

        self._arrow.image.anchor_x = self._arrow.image.width // 2
        self._arrow.image.anchor_y = self._arrow.image.height // 2
        self._arrow.scale = 0.4

        self.update_vertices()
        self.update()

    def update(self):
        """ Update child power an connection line colour """
        self._child.update_power()

        if self._parent.powered:
            self._line.colors = (255, 76, 76, 255, 76, 76)
            self._arrow.image = pgl.image.load('resources/connection_direction_powered.png')
        else:
            self._line.colors = (150, 150, 150, 150, 150, 150)
            self._arrow.image = pgl.image.load('resources/connection_direction.png')

        self._arrow.image.anchor_x = self._arrow.image.width // 2
        self._arrow.image.anchor_y = self._arrow.image.height // 2
        self._arrow.scale = 0.4

    def update_vertices(self):
        """ Update connection vertex positions """
        self._line.vertices = (self._parent.x, self._parent.y, self._child.x, self._child.y)

        # direction arrow
        self._arrow.update(x=self._parent.x + (self._child.x - self._parent.x) // 2,
                           y=self._parent.y + (self._child.y - self._parent.y) // 2,
                           rotation=atan2(self._child.y - self._parent.y,
                                          self._child.x - self._parent.x) * -180 / pi + 90)

    def get_child(self):
        """ Get child node """
        return self._child

    def delete(self):
        """ Remove connection references between parent and child """
        if not self._deleted:
            self._deleted = True

            self._line.delete()
            self._arrow.delete()
            self._child.remove_source(self._parent)
            self._parent.remove_child(self)


class Node(pgl.sprite.Sprite):
    def __init__(self, x, y, view_x, view_y, scale, batch=None):
        super().__init__(pgl.image.load('resources/Node.png'), view_x, view_y, batch=batch,
                         group=pgl.graphics.OrderedGroup(2))

        self.scale = scale
        self.pos_x = x
        self.pos_y = y
        self.children = []
        self.sources = []
        self.powered = False

        self._power_overlay = pgl.sprite.Sprite(pgl.image.load('resources/Node_power.png'), view_x, view_y,
                                                batch=batch, group=pgl.graphics.OrderedGroup(3))
        self._power_overlay.visible = False
        self._power_overlay.scale = scale

        self._selected_overlay = pgl.sprite.Sprite(pgl.image.load('resources/Node_select.png'), view_x, view_y,
                                                   batch=batch, group=pgl.graphics.OrderedGroup(3))
        self._selected_overlay.visible = False
        self._selected_overlay.scale = scale

        self._center_image()

    def _center_image(self):
        """ set anchor points of image to be on x, y """
        self.image.anchor_x = self.image.width // 2
        self.image.anchor_y = self.image.height // 2
        self.update()

        if self._power_overlay:
            self._power_overlay.image.anchor_x = self._power_overlay.image.width // 2
            self._power_overlay.image.anchor_y = self._power_overlay.image.height // 2
            self._power_overlay.update()

        if self._selected_overlay:
            self._selected_overlay.image.anchor_x = self._selected_overlay.image.width // 2
            self._selected_overlay.image.anchor_y = self._selected_overlay.image.height // 2
            self._selected_overlay.update()

    def move_icon(self, x, y, absolute=False):
        """ Move sprite & overlay sprites by x, y or to x, y if absolute. """
        if absolute:
            self.x = x
            self.y = y
        else:
            self.x += x
            self.y += y

        # move overlay sprites if they exist
        if self._power_overlay:
            self._power_overlay.x = self.x
            self._power_overlay.y = self.y

        if self._selected_overlay:
            self._selected_overlay.x = self.x
            self._selected_overlay.y = self.y

        # move connection line for all connections
        self.update_connections()

        for source in self.sources:
            source.update_connections()

    def update_connections(self):
        """ update the vertices of all children """
        for child in self.children:
            child.update_vertices()

    def update_power(self):
        """ Update powered state by checking all sources to see if they are powered,
        if any are, then powered is true """
        prev_power = self.powered

        self.powered = False
        if any([source.powered for source in self.sources]): self.powered = True

        # preform updates only if power state has changed
        if self.powered != prev_power:
            if self.powered:
                self._power_overlay.visible = True
            else:
                self._power_overlay.visible = False

            for child in self.children:
                child.update()

    def add_source(self, source):
        """ Add power source to sources if it is not already in sources """
        if source not in self.sources: self.sources.append(source)

    def remove_source(self, source, remove_from_list=False):
        """ Remove source if it is in sources
         remove_from_list should be false unless this node is not being deleted """
        if source in self.sources:

            if remove_from_list: self.sources.remove(source)
            source.remove_child(self)

    def add_child(self, new_child):
        """ Create new child object if child is not already in children """
        for child in self.children:
            if child.get_child() is new_child or child.get_child() is self:
                return

        self.children.append(_Child(self, new_child, self.batch))

    def remove_child(self, child_obj, remove_from_list = False):
        """ Remove child from children
         remove_from_list should be false unless this node is not being deleted"""
        # if child_obj is _Child class
        if type(child_obj) == _Child and child_obj in self.children:
            if remove_from_list: self.children.remove(child_obj)
            child_obj.delete()

        # if child_obj is child node
        else:
            for child in self.children:
                if child.get_child() == child_obj:
                    if remove_from_list: self.children.remove(child)
                    child.delete()

    def select(self, x=None, y=None, highlight=True):
        """ Draw selected overlay & return if x, y is within sprite """
        self.pos_x = self.x
        self.pos_y = self.y

        if x is None and y is None:
            if highlight:
                self._selected_overlay.visible = True
            return True

        if self.x - self.width // 2 < x < self.x + self.width // 2 and self.y - self.height // 2 < y < self.y + self.height // 2:
            if highlight:
                self._selected_overlay.visible = True

            return True
        return False

    def deselect(self):
        """ Remove select overlay """
        self._selected_overlay.visible = False

    def show(self):
        """ set sprite to visible """
        self.visible = True
        if self.powered and self._power_overlay: self._power_overlay.visible = True

    def hide(self):
        """ set sprite to invisible """
        self.visible = False
        if self._power_overlay: self._power_overlay.visible = False

    def delete(self):
        """ Delete self and remove child and source references """
        for child in self.children: child.delete()
        for source in self.sources: self.remove_source(source)

        self._selected_overlay.delete()
        if self._power_overlay: self._power_overlay.delete()

        super().delete()
