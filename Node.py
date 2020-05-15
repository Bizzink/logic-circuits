import pyglet as pgl


class _Child:
    """ Handles connections between nodes """
    def __init__(self, parent, child, batch, draw_line=True):
        child.add_source(parent)
        child.update_power()

        self._child = child
        self._parent = parent
        self._line = None

        self._deleted = False

        if draw_line:
            self._line = batch.add(2, pgl.gl.GL_LINES, None,
                                   ('v2i', (parent.x + parent.width // 2, parent.y + parent.height // 2,
                                            child.x + child.width // 2, child.y + child.height // 2)),
                                   ('c3B', (150, 150, 150, 150, 150, 150)))

        self.update()

    def update(self):
        """ Update child power an connection line colour """
        self._child.update_power()

        if self._parent.powered:
            self._line.colors = (255, 76, 76, 255, 76, 76)
        else:
            self._line.colors = (150, 150, 150, 150, 150, 150)

    def update_vertices(self):
        """ Update connection vertex positions """
        if self._line is not None:
            self._line.vertices = (self._parent.x + self._parent.width // 2, self._parent.y + self._parent.height // 2,
                                   self._child.x + self._child.width // 2, self._child.y + self._child.height // 2)

    def get_child(self):
        """ Get child node """
        return self._child

    def delete(self):
        """ Remove connection references between parent and child """
        if not self._deleted:
            self._deleted = True

            self._line.delete()
            self._child.remove_source(self._parent)
            self._parent.remove_child(self)


class Node(pgl.sprite.Sprite):
    def __init__(self, x, y, view_x, view_y, scale, batch=None):
        super().__init__(pgl.image.load('resources/Node.png'), view_x, view_y, batch=batch)
        self.scale = scale
        self._pos_x = x  # needed ?
        self._pos_y = y
        self.children = []
        self.sources = []
        self.powered = False

        self._power_overlay = pgl.sprite.Sprite(pgl.image.load('resources/Node_power.png'), view_x, view_y,
                                                batch=batch, group=pgl.graphics.OrderedGroup(2))
        self._power_overlay.opacity = 0
        self._power_overlay.scale = scale

        self._selected_overlay = pgl.sprite.Sprite(pgl.image.load('resources/Node_select.png'), view_x, view_y,
                                                   batch=batch)
        self._selected_overlay.opacity = 0
        self._selected_overlay.scale = scale

    def move_icon(self, x, y, absolute=False):
        """ Move sprite & overlay sprites by x, y or to x, y if absolute. """
        if absolute:
            self.x = x
            self.y = y
        else:
            self.x += x
            self.y += y

        # move overlay sprites if they exist
        if self._power_overlay is not None:
            self._power_overlay.x = self.x
            self._power_overlay.y = self.y

        if self._selected_overlay is not None:
            self._selected_overlay.x = self.x
            self._selected_overlay.y = self.y

        # move connection line for all children
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
                self._power_overlay.opacity = 255
            else:
                self._power_overlay.opacity = 0

            for child in self.children:
                child.update()

    def add_source(self, source):
        """ Add power source to sources if it is not already in sources """
        if source not in self.sources: self.sources.append(source)

    def remove_source(self, source, remove_from_list = False):
        """ Remove source if it is in sources
         remove_from_list should be false unless this node is not being deleted """
        if source in self.sources:

            if remove_from_list: self.sources.remove(source)
            source.remove_child(self)

    def add_child(self, new_child, draw_connection=True):
        """ Create new child object if child is not already in children """
        for child in self.children:
            if child.get_child() is new_child or child.get_child() is self:
                return

        self.children.append(_Child(self, new_child, self.batch, draw_connection))

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

    def select(self, x, y, highlight=True):
        """ Draw selected overlay & return if x, y is within sprite """
        if self.x < x < self.x + self.width and self.y < y < self.y + self.height:
            if highlight:
                self._selected_overlay.opacity = 255
            return True
        return False

    def deselect(self):
        """ Remove select overlay """
        self._selected_overlay.opacity = 0

    def delete(self):
        """ Delete self and remove child and source references """
        for child in self.children: child.delete()
        for source in self.sources: self.remove_source(source)

        self._selected_overlay.delete()
        if self._power_overlay is not None: self._power_overlay.delete()

        super().delete()
