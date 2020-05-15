import pyglet as pgl
from pyglet.window import mouse, key
from Node import Node
from Inverter import Inverter
from Switch import Switch


class View:
    def __init__(self, x=0, y=0):
        self.x = x
        self.y = y
        self.scale = 0.15
        self.objects = []
        self.selected_objects = []
        self.mouse_pos = [0, 0]
        self.dragged = False
        self.drag_dist = 0
        self.creating_connection = False
        self.selected = None
        self.parent_Node = None

    def move(self, dx, dy):
        self.x += dx
        self.y += dy

        for obj in self.objects:
            obj.move_icon(dx, dy)

    def change_scale(self, scale):
        self.scale += scale

    def add_object(self, obj):
        self.objects.append(obj)

    def select(self, x, y):
        select = False
        self.selected_objects.clear()

        for obj in self.objects:
            if type(obj) == Switch:
                if obj.select(x, y, False):
                    obj.flip()
                    return False

            obj.deselect()

            if obj.select(x, y):
                self.selected_objects.append(obj)
                select = True

        return select

    def select_multiple(self, x, y):
        for obj in self.objects:
            if obj.select(x, y):
                if obj in self.selected_objects:
                    obj.deselect()
                    self.selected_objects.remove(obj)
                else:
                    self.selected_objects.append(obj)

    def get_node(self, x, y):
        for obj in self.objects:
            if obj.select(x, y, highlight = False):
                return obj
        return None


window = pgl.window.Window(1280, 720, resizable = True)
window.set_minimum_size(400, 400)
main_batch = pgl.graphics.Batch()
view = View(x = window.width // 2, y = window.height // 2)
pgl.gl.glLineWidth(3)


@window.event
def on_key_press(symbol, modifiers):
    # _(num) is not protected, _ is to make the name valid
    if view.selected is not None and symbol in [key._1, key._2]:
        view.selected.delete()

    if symbol == key._1:
        view.selected = None
        window.set_mouse_visible(True)

    elif symbol == key._2:
        view.selected = Node(0, 0, view.mouse_pos[0], view.mouse_pos[1], view.scale, batch = main_batch)
        view.selected.opacity = 128
        window.set_mouse_visible(False)

    elif symbol == key._3:
        view.selected = Inverter(0, 0, view.mouse_pos[0], view.mouse_pos[1], view.scale, batch = main_batch)
        view.selected.opacity = 128
        window.set_mouse_visible(False)

    elif symbol == key._4:
        view.selected = Switch(0, 0, view.mouse_pos[0], view.mouse_pos[1], view.scale, batch = main_batch)
        view.selected.opacity = 128
        window.set_mouse_visible(False)

    elif symbol == key.DELETE:
        for obj in view.selected_objects:
            obj.delete()
            view.objects.remove(obj)
        view.selected_objects.clear()


@window.event
def on_mouse_leave(x, y):
    if view.selected is not None:
        view.selected.opacity = 0


@window.event
def on_mouse_enter(x, y):
    if view.selected is not None:
        view.selected.opacity = 128


@window.event
def on_mouse_motion(x, y, dx, dy):
    view.mouse_pos = [x, y]

    if view.selected is not None:
        try:
            view.selected.move_icon(x - view.selected.width // 2, y - view.selected.height // 2, absolute = True)
        except AttributeError:
            pass


@window.event
def on_mouse_drag(x, y, dx, dy, button, modifiers):
    view.mouse_pos = [x, y]
    view.drag_dist += dx + dy

    if abs(view.drag_dist) > 10:
        view.dragged = True

    if view.selected is not None:
        window.set_mouse_visible(True)
        view.selected.opacity = 0
    
    if button == mouse.LEFT and not view.creating_connection:
        view.move(dx, dy)


@window.event
def on_mouse_press(x, y, button, modifiers):
    view.parent_Node = view.get_node(x, y)
    if view.parent_Node is not None: view.creating_connection = True


@window.event
def on_mouse_release(x, y, button, modifiers):

    if view.selected is not None:
        view.selected.opacity = 128
        window.set_mouse_visible(False)

    if view.dragged and view.creating_connection:
        child = view.get_node(x, y)

        if child is not None:
            view.parent_Node.add_child(child)

    elif not view.dragged and button == mouse.LEFT:
        if modifiers and key.MOD_SHIFT:
            view.select_multiple(x, y)

        elif not view.select(x, y):
            if view.selected is not None:
                if type(view.selected) == Node:
                    obj = Node(x - view.x, y - view.y, x, y, view.scale, batch = main_batch)

                elif type(view.selected) == Inverter:
                    obj = Inverter(x - view.x, y - view.y, x, y, view.scale, batch = main_batch)

                elif type(view.selected) == Switch:
                    obj = Switch(x - view.x, y - view.y, x, y, view.scale, batch = main_batch)

                obj.move_icon(-obj.width // 2, -obj.height // 2)
                view.add_object(obj)

    view.dragged = False
    view.drag_dist = 0
    view.creating_connection = False


@window.event
def on_mouse_scroll(x, y, scroll_x, scroll_y):
    pass
    # if 0.1 <= view.scale + scroll_y * 0.1 < 1:
    #    view.change_scale(scroll_y * 0.1)
    #     view.scale = max(view.scale + scroll_y, 1)
    #     x -= int(window.width / 2)
    #     y -= int(window.width / 2)
    #
    #     view.x += x - (x * view.scale) - view.scale / 2
    #     view.y += y - (y * view.scale) - view.scale / 2


@window.event
def on_draw():
    window.clear()

    pgl.graphics.draw(2, pgl.gl.GL_LINES, ('v2i', (view.x, 0, view.x, window.height)), ('c3B', (50, 50, 50, 50, 50, 50)))
    pgl.graphics.draw(2, pgl.gl.GL_LINES, ('v2i', (0, view.y, window.width, view.y)), ('c3B', (50, 50, 50, 50, 50, 50)))

    if view.creating_connection and view.dragged:
        pgl.graphics.draw(2, pgl.gl.GL_LINES,
                          ('v2i', (view.parent_Node.x + view.parent_Node.width // 2,
                                   view.parent_Node.y + view.parent_Node.height // 2,
                                   view.mouse_pos[0], view.mouse_pos[1])),
                          ('c3B', (100, 100, 100, 100, 100, 100)))

    main_batch.draw()


if __name__ == '__main__':
    pgl.app.run()
