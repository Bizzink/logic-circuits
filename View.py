from math import sqrt
import pyglet as pgl
from Switch import Switch


class MousePos:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def pos(self, x, y):
        self.x = x
        self.y = y


def _line(vertices, colour=(25, 25, 25)):
    """ draw a line """
    pgl.graphics.draw(2, pgl.gl.GL_LINES, ('v2i', vertices), ('c3B', colour * 2))


class View:
    def __init__(self, window):
        self.x = 0
        self.y = 0

        self._scale = 1
        self._obj_scale = 0.15
        self._min_scale = 0.3
        self._max_scale = 2
        self._grid_size = 25

        self._window = window
        self.batch = pgl.graphics.Batch()
        self._current_obj_batch = pgl.graphics.Batch()

        self.objects = []
        self.selected_objects = []
        self.current_obj = None
        self.parent_obj = None

        self.creating_connection = False
        self.select_box = MousePos(None, None)
        self.keep_selected = False
        self.held_copy = None
        self.creating_subcircuit = False

        # pyglet has no way of directly getting mouse pos, so it is tracked using this
        self.mouse = MousePos(0, 0)

    def draw(self):
        """ draw all items to screen, draw overlays """
        self._draw_grid()

        if self.creating_connection:
            x, y = self.screen_pos(self.parent_obj.x, self.parent_obj.y)
            _line((x, y, self.mouse.x, self.mouse.y), (100, 100, 100))

        # draw objects
        pgl.gl.glTranslatef(self.x + self._window.width // 2, self.y + self._window.height // 2, 0)
        pgl.gl.glScalef(self._scale, self._scale, 0)

        self.batch.draw()

        pgl.gl.glScalef(1 / self._scale, 1 / self._scale, 0)
        pgl.gl.glTranslatef(-self.x - self._window.width // 2, -self.y - self._window.height // 2, 0)

        if self.select_box_size(self.mouse.x, self.mouse.y) > 5:
            # draw a box to represent the selection area
            x, y = self.screen_pos(self.select_box.x, self.select_box.y)

            _line((x, y, self.mouse.x, y), (20, 255, 100))
            _line((x, y, x, self.mouse.y), (20, 255, 100))
            _line((x, self.mouse.y, self.mouse.x, self.mouse.y), (20, 255, 100))
            _line((self.mouse.x, y, self.mouse.x, self.mouse.y), (20, 255, 100))

        if self.current_obj:
            x, y = self.grid_pos(self.mouse.x, self.mouse.y)
            self.current_obj.move_icon(x, y, absolute=True)
            self._current_obj_batch.draw()

    def _draw_grid(self):
        """ draw background grid, x & y axis """
        # only draw grid if it is not too small (< 0.3)
        if self._scale > 0.3:
            pgl.gl.glLineWidth(1)
            grid_size = int(self._grid_size * self._scale)

            # draw vertical lines
            for i in range(self._window.width // grid_size + 3):
                _line((i * grid_size + (self.x + self._window.width // 2) % grid_size, 0,
                       i * grid_size + (self.x + self._window.width // 2) % grid_size, self._window.height))

            # draw horizontal lines
            for i in range(self._window.height // grid_size + 3):
                _line((0, i * grid_size + (self.y + self._window.height // 2) % grid_size,
                       self._window.width, i * grid_size + (self.y + self._window.height // 2) % grid_size))

        # draw x, y axis
        pgl.gl.glLineWidth(3)
        _line((self.x + self._window.width // 2, 0, self.x + self._window.width // 2, self._window.height))
        _line((0, self.y + self._window.height // 2, self._window.width, self.y + self._window.height // 2))

    def grid_pos(self, x, y):
        """ return (x, y) of closest grid pos to provided x, y """
        grid_size = self._grid_size * self._scale

        # remove grid offset
        x -= (self.x + self._window.width // 2) % grid_size
        y -= (self.y + self._window.height // 2) % grid_size

        # get closest point
        x = grid_size * round(float(x) / grid_size)
        y = grid_size * round(float(y) / grid_size)

        # add grid offset
        x += (self.x + self._window.width // 2) % grid_size
        y += (self.y + self._window.height // 2) % grid_size

        return x, y

    def world_pos(self, screen_x, screen_y, grid_pos=False):
        """ get the world pos of the screen space x, y """
        if grid_pos: screen_x, screen_y = self.grid_pos(screen_x, screen_y)

        x = int((screen_x - self._window.width // 2 - self.x) // self._scale)
        y = int((screen_y - self._window.height // 2 - self.y) // self._scale)

        return x, y

    def screen_pos(self, world_x, world_y):
        """ get the screen pos of the world space x, y """
        x = int(world_x * self._scale + self.x + self._window.width // 2)
        y = int(world_y * self._scale + self.y + self._window.height // 2)

        return x, y

    def move(self, dx, dy):
        """ move view around """
        self.x += dx
        self.y += dy

    def scale(self, scale_change):
        """ change scale """
        current_scale = self._scale
        self._scale += scale_change * 0.1

        # clamp scale between min_scale, max_scale
        if self._scale < self._min_scale: self._scale = self._min_scale
        if self._scale > self._max_scale: self._scale = self._max_scale

        # move world so that scale is centered on mouse pos
        self.x += int((self.mouse.x - self._window.width // 2 - self.x) * (current_scale - self._scale))
        self.y += int((self.mouse.y - self._window.height // 2 - self.y) * (current_scale - self._scale))

        # rescale current obj preview
        if self.current_obj: self.current_obj.scale = self._scale * self._obj_scale

    def get_scale(self):
        """ temporary """
        return self._scale

    def set_object(self, obj_type):
        """ set current_obj to obj_type, create sprite if obj_type is not None """
        if self.current_obj: self.current_obj.delete()
        self.current_obj = None
        self._window.set_mouse_visible(True)

        if obj_type:
            self._window.set_mouse_visible(False)
            self.current_obj = obj_type(self.mouse.x, self.mouse.y, self._scale * self._obj_scale,
                                        self._current_obj_batch)
            self.current_obj.opacity = 128

    def place_object(self, x, y):
        """ place current object at x, y if there isn't one there already """
        x, y = self.world_pos(x, y, grid_pos=True)

        if self.get_obj(x, y) is None:
            # create new object of same type as current_obj
            obj = type(self.current_obj).__new__(type(self.current_obj))
            obj.__init__(x, y, self._obj_scale, self.batch)

            self.objects.append(obj)

    def select(self, x, y):
        """ select object at x, y add it to selected objects list (all other selected objects are deselected) """
        self.deselect_all()

        x, y = self.world_pos(x, y)

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

    def select_multiple(self, x=None, y=None, obj = None):
        """ toggle select on object at x, y """
        if x and y:
            x, y = self.world_pos(x, y)

            for obj in self.objects:
                if obj.select(x, y, highlight = False):
                    if obj in self.selected_objects:
                        obj.deselect()
                        self.selected_objects.remove(obj)
                    else:
                        self.selected_objects.append(obj)

        else:
            if obj in self.selected_objects:
                obj.deselect()
                self.selected_objects.remove(obj)
            else:
                obj.select()
                self.selected_objects.append(obj)

    def select_area(self, x, y):
        """ select all objects in region between self.select_box and x, y """
        x, y = self.world_pos(x, y)
        self.deselect_all()

        x1 = min(self.select_box.x, x)
        y1 = min(self.select_box.y, y)
        x2 = max(self.select_box.x, x)
        y2 = max(self.select_box.y, y)

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
        x, y = self.world_pos(x, y)

        if self.select_box.x is not None: return sqrt((self.select_box.x - x) ** 2 + (self.select_box.y - y) ** 2)
        return 0

    def duplicate(self):
        """ duplicate selected objects into held_copy """
        if self.held_copy or len(self.selected_objects) == 0: return

        self.held_copy = []
        object_children = []

        for obj in self.selected_objects:
            # create new instance of object
            obj_copy = type(obj).__new__(type(obj))
            obj_copy.__init__(obj.x, obj.y, self._obj_scale, self.batch)

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
        x, y = self.world_pos(x, y)

        for obj in self.objects:
            if obj.select(x, y, highlight=False): return obj
        return None
