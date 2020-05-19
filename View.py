from math import sqrt
import pyglet as pgl
from Switch import Switch


class View:
    def __init__(self, x, y, window, batch):
        self.x = x
        self.y = y
        self.scale = 0.15
        self._grid_size = 25
        self._window = window
        self._batch = batch

        self.objects = []
        self.selected_objects = []
        self.current_obj = None
        self.parent_obj = None

        self.creating_connection = False
        self.select_box = None
        self.keep_selected = False
        self.held_copy = None

        # pyglet has no way of directly getting mouse pos, so it is tracked using this
        self.mouse_pos = [0, 0]

    def move(self, dx, dy):
        """ move view around """
        self.x += dx
        self.y += dy

        for obj in self.objects:
            obj.move_icon(dx, dy)

    def change_scale(self, scale):
        self.scale += scale

    def place_object(self, x, y):
        """ place current object at x, y if there isn't one there already """
        x, y = self.grid_pos(x, y)

        if self.get_obj(x, y) is None:
            # create new object of same type as current_obj
            obj = type(self.current_obj).__new__(type(self.current_obj))
            obj.__init__(x - self.x, y - self.y, x, y, self.scale, batch = self._batch)

            self.objects.append(obj)

    def select(self, x, y):
        """ select object at x, y add it to selected objects list (all other selected objects are deselected) """
        self.deselect_all()

        for obj in self.objects:
            # if clicked obj is switch, flip switch instead of selecting
            if type(obj) == Switch:
                if obj.select(x, y, False):
                    obj.flip()
                    return False

            if obj.select(x, y):
                self.selected_objects.append(obj)
                return True

        return False

    def select_multiple(self, x, y):
        """ toggle select on object at x, y """
        for obj in self.objects:
            if obj.select(x, y):
                if obj in self.selected_objects:
                    obj.deselect()
                    self.selected_objects.remove(obj)
                else:
                    self.selected_objects.append(obj)

    def select_area(self, x, y):
        """ select all objects in region between self.select_box and x, y """
        for obj in self.selected_objects:
            obj.deselect()

        self.selected_objects.clear()

        x1 = min(self.select_box[0], x)
        y1 = min(self.select_box[1], y)
        x2 = max(self.select_box[0], x)
        y2 = max(self.select_box[1], y)

        for obj in self.objects:
            if obj.x + obj.width // 2 > x1 and obj.x - obj.width // 2 < x2 \
                    and obj.y + obj.height // 2 > y1 and obj.y - obj.height // 2 < y2:

                obj.select()
                self.selected_objects.append(obj)

    def deselect_all(self):
        """ deselect all selected objects """
        for obj in self.selected_objects:
            obj.deselect()

        self.selected_objects.clear()

    def select_box_size(self, x, y):
        """ get current diagonal size of selection box """
        if self.select_box is not None:
            return sqrt((self.select_box[0] - x) ** 2 + (self.select_box[1] - y) ** 2)
        return 0

    def duplicate(self):
        """ duplicate selected objects into held_copy """
        if self.held_copy or len(self.selected_objects) == 0: return

        self.held_copy = []
        object_children = []

        for obj in self.selected_objects:
            # create new instance of object
            obj_copy = type(obj).__new__(type(obj))
            obj_copy.__init__(obj.x, obj.y, obj.x, obj.y, self.scale, batch = self._batch)

            self.held_copy.append(obj_copy)
            self.objects.append(obj_copy)

            obj_children = []

            for child in obj.children:
                child = child.get_child()
                if child in self.selected_objects:
                    obj_children.append(self.selected_objects.index(child))

            object_children.append(obj_children)

        self.deselect_all()

        for ind, obj in enumerate(self.held_copy):
            for child in object_children[ind]:
                obj.add_child(self.held_copy[child])

            obj.select()
            self.selected_objects.append(obj)

    def get_obj(self, x, y):
        """ return the object at (screen) x, y if it exists """
        for obj in self.objects:
            if obj.select(x, y, highlight = False):
                return obj
        return None

    def grid_pos(self, x, y):
        """ return (x, y) of closest grid pos to provided x, y
         if sprite is not None, offset so sprite is centered on grid pos """
        x = self._grid_size * round(float(x - self.x) / self._grid_size)
        y = self._grid_size * round(float(y - self.y) / self._grid_size)

        return x + self.x, y + self.y

    def draw_grid(self):
        """ draw background grid """
        def draw(vertices, colour = (25, 25, 25, 25, 25, 25)):
            pgl.graphics.draw(2, pgl.gl.GL_LINES, ('v2i', vertices), ('c3B', colour))

        pgl.gl.glLineWidth(1)

        # draw vertical lines
        for i in range(self._window.width // self._grid_size + 1):
            draw((i * self._grid_size + self.x % self._grid_size, 0,
                  i * self._grid_size + self.x % self._grid_size, self._window.height))

        # draw horizontal lines
        for i in range(self._window.height // self._grid_size + 1):
            draw((0, i * self._grid_size + self.y % self._grid_size,
                  self._window.width, i * self._grid_size + self.y % self._grid_size))

        pgl.gl.glLineWidth(2)

        # draw x, y axis
        draw((self.x, 0, self.x, self._window.height), colour=(50, 50, 50, 50, 50, 50))
        draw((0, self.y, self._window.width, self.y), colour=(50, 50, 50, 50, 50, 50))
