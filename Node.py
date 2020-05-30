from math import atan2, pi
import pyglet as pgl


class _Child:
    """ Handles connections between nodes """

    def __init__(self, parent, child, batch):
        child.add_source(parent)

        self._child = child
        self._parent = parent
        self._selected = False
        self.deleted = False

        self._line = batch.add(2, pgl.gl.GL_LINES, None, ('v2i', (0, 0, 0, 0)), ('c3B', (150, 150, 150, 150, 150, 150)))
        self._arrow = pgl.sprite.Sprite(pgl.image.load('resources/connection_direction_unpowered.png'), batch=batch)

        self.update()
        self.update_vertices()

    def update(self):
        """ Update child power an connection line colour """
        self._child.update_power()

        if self._selected:
            self._line.colors = (1, 212, 255, 1, 212, 255)
            self._arrow.image = pgl.image.load('resources/connection_direction_selected.png')

        else:
            if self._parent.powered:
                self._line.colors = (255, 76, 76, 255, 76, 76)
                self._arrow.image = pgl.image.load('resources/connection_direction_powered.png')
            else:
                self._line.colors = (150, 150, 150, 150, 150, 150)
                self._arrow.image = pgl.image.load('resources/connection_direction_unpowered.png')

        self._arrow.image.anchor_x = self._arrow.image.width // 2
        self._arrow.image.anchor_y = self._arrow.image.height // 2
        self._arrow.scale = 0.25

    def update_vertices(self):
        """ Update connection vertex positions """
        # line
        self._line.vertices = (self._parent.x, self._parent.y, self._child.x, self._child.y)

        # direction arrow
        self._arrow.update(x=self._parent.x + (self._child.x - self._parent.x) // 2,
                           y=self._parent.y + (self._child.y - self._parent.y) // 2,
                           rotation=atan2(self._child.y - self._parent.y,
                                          self._child.x - self._parent.x) * -180 / pi + 90)

    def select(self, x, y):
        """ check if x, y is within arrow sprite, select and return if true """
        if self._arrow.x - self._arrow.width / 2 < x < self._arrow.x + self._arrow.width / 2 and \
                self._arrow.y - self._arrow.height / 2 < y < self._arrow.y + self._arrow.height / 2:
            self._selected = True
            self.update()
            return True

        return False

    def deselect(self):
        """ deselect and revert colours """
        self._selected = False
        self.update()

    def get_child(self):
        """ Get child node """
        return self._child

    def delete(self):
        """ Remove connection references between parent and child """
        if not self.deleted:
            self.deleted = True
            self._line.delete()
            self._arrow.delete()
            self._child.remove_source(self._parent)
            self._parent.remove_child(self)


class Node(pgl.sprite.Sprite):
    def __init__(self, x, y, scale, batch):
        image = pgl.image.load(f"resources/{type(self).__name__}_unpowered_unselected.png")
        super().__init__(image, x, y, batch=batch, group=pgl.graphics.OrderedGroup(2))

        self.scale = scale

        self.children = []
        self.sources = []
        self.powered = False
        self.selected = False

        self._update_image()

        # for tracking x, y when moving icon while snapping to grid
        self.pos_x, self.pos_y = x, y

    def __str__(self):
        return f"{type(self).__name__}(x={self.x}, y={self.y}, powered={self.powered}, {len(self.children)} children, {len(self.sources)} sources)"

    def _update_image(self):
        """ set image based on selected, powered state """
        powered = "powered" if self.powered else "unpowered"
        selected = "selected" if self.selected else "unselected"

        self.image = pgl.image.load(f"resources/{type(self).__name__}_{powered}_{selected}.png")

        # center image anchor point
        self.image.anchor_x = self.image.width // 2
        self.image.anchor_y = self.image.height // 2
        self.update()

    def update_connection_vertices(self):
        """ update the vertices of all children """
        for child in self.children: child.update_vertices()

    def move_icon(self, x, y, absolute=False):
        """ Move sprite & overlay sprites by x, y or to x, y if absolute. """
        if absolute:
            self.x = x
            self.y = y
        else:
            self.x += x
            self.y += y

        # move connection line for all connections
        self.update_connection_vertices()
        for source in self.sources: source.update_connection_vertices()

    def move_pos(self, dx = None, dy = None, to_icon = False):
        """ move tracking pos - for use when moving while snapping to grid """
        if to_icon:
            self.pos_x = self.x
            self.pos_y = self.y
        else:
            self.pos_x += dx
            self.pos_y += dy

    def update_power(self):
        """ Update powered state by checking all sources to see if they are powered,
        if any are, then powered is true """
        prev_power = self.powered

        self.powered = False
        if any([source.powered for source in self.sources]): self.powered = True

        # preform updates only if power state has changed
        if self.powered != prev_power:
            self._update_image()
            for child in self.children: child.update()

    def add_source(self, source):
        """ Add power source to sources if it is not already in sources """
        if source not in self.sources: self.sources.append(source)

    def remove_source(self, source):
        """ Remove source if it is in sources """
        if source in self.sources:
            self.sources.remove(source)
            source.remove_child(self)
            self.update_power()

    def add_child(self, new_child):
        """ Create new child object if child is not already in children """
        if new_child is self: return

        for child in self.children:
            if child.get_child() is new_child: return

        self.children.append(_Child(self, new_child, self.batch))

    def remove_child(self, child_obj):
        """ Remove child from children """
        # if child_obj is _Child class
        if type(child_obj) == _Child and child_obj in self.children:
            self.children.remove(child_obj)
            child_obj.delete()

        # if child_obj is child node
        else:
            for child in self.children:
                if child.get_child() == child_obj:
                    self.children.remove(child)
                    child.delete()

    def select(self, x=None, y=None, highlight=True, accept_child = True):
        """ check if x, y is within sprite, select and return if true, otherwise check if any
         child connection lines are selected and return that instead"""
        if x is None and y is None and highlight:
            self.selected = True
            self._update_image()
            return

        if x and self.x - self.width / 2 < x < self.x + self.width / 2 and self.y - self.height / 2 < y < self.y + self.height / 2:
            if highlight:
                self.selected = True
                self._update_image()
            return self

        if accept_child:
            for child in self.children:
                if child.select(x, y): return child

    def deselect(self):
        """ Deselect and change image """
        self.selected = False
        self._update_image()

    def delete(self):
        """ Delete self and remove child and source references """
        while len(self.children) > 0: self.remove_child(self.children[0])
        while len(self.sources) > 0: self.remove_source(self.sources[0])
        super().delete()
