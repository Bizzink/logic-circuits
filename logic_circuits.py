from math import sqrt
import pyglet as pgl
from pyglet.window import mouse, key
from Node import Node
from Inverter import Inverter
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


class LogicCircuits(pgl.window.Window):
    def __init__(self, w, h):
        super().__init__(w, h, resizable=True)
        self.set_minimum_size(600, 400)

        self.x = 0
        self.y = 0

        self.scale = 1
        self.obj_scale = 0.15
        self.min_scale = 0.3
        self.max_scale = 2
        self.grid_size = 25
        self.min_select_box_size = 30

        self.batch = pgl.graphics.Batch()
        self.current_obj_batch = pgl.graphics.Batch()

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

    def set_object(self, obj_type):
        """ set current_obj to obj_type, create sprite if obj_type is not None """
        if self.current_obj: self.current_obj.delete()
        self.current_obj = None
        self.set_mouse_visible(True)

        if obj_type:
            self.set_mouse_visible(False)
            self.current_obj = obj_type(self.mouse.x, self.mouse.y, self.scale * self.obj_scale, self.current_obj_batch)
            self.current_obj.opacity = 128

    def place_object(self, x, y):
        """ place current object at x, y if there isn't one there already """
        x, y = self.world_pos(x, y, grid_pos=True)

        if self.get_obj(x, y) is None:
            # create new object of same type as current_obj
            obj = type(self.current_obj).__new__(type(self.current_obj))
            obj.__init__(x, y, self.obj_scale, self.batch)

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

            obj = obj.select(x, y)

            if obj is not None:
                self.selected_objects.append(obj)
                return True

        return False

    def select_multiple(self, x=None, y=None, obj=None):
        """ toggle select on object at x, y """
        if x and y:
            x, y = self.world_pos(x, y)

            for obj in self.objects:
                obj = obj.select(x, y)

                if obj in self.selected_objects:
                    obj.deselect()
                    self.selected_objects.remove(obj)
                else:
                    self.selected_objects.append(obj)

        elif obj:
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
        for obj in self.selected_objects: obj.deselect()
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
            if type(obj).__name__ == "_Child":
                obj.deselect()
                continue

            # create new instance of object
            obj_copy = type(obj).__new__(type(obj))
            obj_copy.__init__(obj.x, obj.y, self.obj_scale, self.batch)

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
            if obj.select(x, y, highlight=False, accept_child=False): return obj

    # === View related functions ===

    def on_draw(self):
        """ draw all items to screen, draw overlays """
        self.clear()

        self.draw_grid()

        if self.creating_connection:
            x, y = self.screen_pos(self.parent_obj.x, self.parent_obj.y)
            _line((x, y, self.mouse.x, self.mouse.y), (100, 100, 100))

        # draw objects
        pgl.gl.glTranslatef(self.x + self.width // 2, self.y + self.height // 2, 0)
        pgl.gl.glScalef(self.scale, self.scale, 0)

        self.batch.draw()

        pgl.gl.glScalef(1 / self.scale, 1 / self.scale, 0)
        pgl.gl.glTranslatef(-self.x - self.width // 2, -self.y - self.height // 2, 0)

        if self.select_box_size(self.mouse.x, self.mouse.y) > self.min_select_box_size:
            # draw a box to represent the selection area
            x, y = self.screen_pos(self.select_box.x, self.select_box.y)

            _line((x, y, self.mouse.x, y), (20, 255, 100))
            _line((x, y, x, self.mouse.y), (20, 255, 100))
            _line((x, self.mouse.y, self.mouse.x, self.mouse.y), (20, 255, 100))
            _line((self.mouse.x, y, self.mouse.x, self.mouse.y), (20, 255, 100))

        if self.current_obj:
            x, y = self.grid_pos(self.mouse.x, self.mouse.y)
            self.current_obj.move_icon(x, y, absolute=True)
            self.current_obj_batch.draw()

    def draw_grid(self):
        """ draw background grid, x & y axis """
        # only draw grid if it is not too small (< 0.3)
        if self.scale > 0.3:
            pgl.gl.glLineWidth(1)
            grid_size = int(self.grid_size * self.scale)

            # draw vertical lines
            for i in range(self.width // grid_size + 3):
                _line((i * grid_size + (self.x + self.width // 2) % grid_size, 0,
                       i * grid_size + (self.x + self.width // 2) % grid_size, self.height))

            # draw horizontal lines
            for i in range(self.height // grid_size + 3):
                _line((0, i * grid_size + (self.y + self.height // 2) % grid_size,
                       self.width, i * grid_size + (self.y + self.height // 2) % grid_size))

        # draw x, y axis
        pgl.gl.glLineWidth(3)
        _line((self.x + self.width // 2, 0, self.x + self.width // 2, self.height))
        _line((0, self.y + self.height // 2, self.width, self.y + self.height // 2))

    def grid_pos(self, x, y):
        """ return (x, y) of closest grid pos to provided x, y """
        grid_size = self.grid_size * self.scale

        # remove grid offset
        x -= (self.x + self.width // 2) % grid_size
        y -= (self.y + self.height // 2) % grid_size

        # get closest point
        x = grid_size * round(float(x) / grid_size)
        y = grid_size * round(float(y) / grid_size)

        # add grid offset
        x += (self.x + self.width // 2) % grid_size
        y += (self.y + self.height // 2) % grid_size

        return x, y

    def world_pos(self, screen_x, screen_y, grid_pos=False):
        """ get the world pos of the screen space x, y """
        if grid_pos: screen_x, screen_y = self.grid_pos(screen_x, screen_y)

        x = int((screen_x - self.width // 2 - self.x) // self.scale)
        y = int((screen_y - self.height // 2 - self.y) // self.scale)

        return x, y

    def screen_pos(self, world_x, world_y):
        """ get the screen pos of the world space x, y """
        x = int(world_x * self.scale + self.x + self.width // 2)
        y = int(world_y * self.scale + self.y + self.height // 2)

        return x, y

    def move_objects(self, obj_list, dx, dy):
        """ move all objects in obj_list by dx, dy, while snapping to grid """
        for obj in obj_list:
            obj.move_pos(dx // self.scale, dy // self.scale)
            x, y = self.screen_pos(obj.pos_x, obj.pos_y)
            x, y = self.grid_pos(x, y)
            x, y = self.world_pos(x, y)
            obj.move_icon(x, y, absolute=True)

            if dx == 0 and dy == 0: obj.move_pos(to_icon=True)

    # === Mouse related functions ===

    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
        """ change scale """
        current_scale = self.scale
        self.scale += scroll_y * 0.1

        # clamp scale between min_scale, max_scale
        if self.scale < self.min_scale: self.scale = self.min_scale
        if self.scale > self.max_scale: self.scale = self.max_scale

        # move world so that scale is centered on mouse pos
        self.x += int((x - self.width // 2 - self.x) * (current_scale - self.scale))
        self.y += int((y - self.height // 2 - self.y) * (current_scale - self.scale))

        # rescale current obj preview
        if self.current_obj: self.current_obj.scale = self.scale * self.obj_scale

    def on_mouse_leave(self, x, y):
        """ hide current obj """
        if self.current_obj: self.current_obj.visible = False

    def on_mouse_enter(self, x, y):
        """ show current obj """
        self.mouse.pos(x, y)

        if self.current_obj: self.current_obj.visible = True

    def on_mouse_motion(self, x, y, dx, dy):
        """ move held objects if they exist """
        self.mouse.pos(x, y)
        if self.held_copy: self.move_objects(self.held_copy, dx, dy)

    def on_mouse_drag(self, x, y, dx, dy, button, modifiers):
        self.mouse.pos(x, y)

        # move selected objects
        if button == mouse.LEFT:
            if len(self.selected_objects) > 0:
                self.keep_selected = True
                self.set_mouse_visible(False)
                self.move_objects(self.selected_objects, dx, dy)

        # move view around
        if button == mouse.RIGHT:
            self.x += dx
            self.y += dy

    def on_mouse_press(self, x, y, button, modifiers):
        # if right click, set cursor to look like movement cursor
        if button == mouse.RIGHT: self.set_mouse_cursor(self.get_system_mouse_cursor(self.CURSOR_SIZE))

        if button == mouse.LEFT and not self.held_copy:
            # if object at mouse, set it as potential parent
            obj = self.get_obj(x, y)

            if obj and not (modifiers and key.MOD_SHIFT):
                if obj not in self.selected_objects:
                    self.parent_obj = obj
                    self.creating_connection = True
                    self.deselect_all()

            # if nothing at mouse, deselect all and start selection box
            else:
                if not (modifiers and key.MOD_SHIFT): self.deselect_all()
                x, y = self.world_pos(x, y)
                self.select_box.pos(x, y)

    def on_mouse_release(self, x, y, button, modifiers):
        # reset cursor
        self.set_mouse_cursor(self.get_system_mouse_cursor(self.CURSOR_DEFAULT))
        if not self.current_obj: self.set_mouse_visible(True)

        if button == mouse.LEFT:
            # finalise moved object positions to their closest grid pos
            if self.held_copy:
                self.move_objects(self.held_copy, 0, 0)
                self.held_copy = None

            elif self.selected_objects:
                self.move_objects(self.selected_objects, 0, 0)

            obj = self.get_obj(x, y)

            if obj:
                # add currently hovered object as child to potential parent if one exists
                if self.creating_connection and obj is not self.parent_obj: self.parent_obj.add_child(obj)

                # otherwise if no parent exists, select currently hovered object
                else:
                    if modifiers and key.MOD_SHIFT:  self.select_multiple(obj=obj)
                    elif not self.keep_selected:

                        self.select(x, y)

            elif not self.creating_connection:
                if not self.keep_selected: self.deselect_all()

                # select all in selected area if area is big enough
                if self.select_box_size(x, y) > self.min_select_box_size:
                    self.select_area(x, y)
                    self.select_box.pos(None, None)

                # place new object if no other conditions are met
                elif self.current_obj: self.place_object(x, y)

            self.creating_connection = False
            self.select_box.pos(None, None)
            self.keep_selected = False

    # === Keyboard related functions ===

    def on_key_press(self, symbol, modifiers):
        if modifiers:
            if key.MOD_CTRL:
                if symbol == key.D:
                    self.duplicate()

                # if symbol == key.G:
                #     subcircuit = Subcircuit(self)
                #     self.objects.append(subcircuit)
                #     self.held_copy = [subcircuit]

        else:
            # object selector
            # _(num) is not protected, _ is to make the name valid
            if symbol == key._1:
                self.set_object(None)
            elif symbol == key._2:
                self.set_object(Node)
            elif symbol == key._3:
                self.set_object(Inverter)
            elif symbol == key._4:
                self.set_object(Switch)

            # delete selected objects
            elif symbol == key.DELETE:
                for obj in self.selected_objects:
                    obj.delete()
                    if obj in self.objects: self.objects.remove(obj)
                self.selected_objects.clear()

            # reset self to origin
            elif symbol == key.O:
                self.x = 0
                self.y = 0
                self.scale = 1


if __name__ == '__main__':
    window = LogicCircuits(1280, 720)
    pgl.app.run()
