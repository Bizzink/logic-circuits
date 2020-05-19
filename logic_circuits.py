import pyglet as pgl
from pyglet.window import mouse, key
from Node import Node
from Inverter import Inverter
from Switch import Switch
from View import View

window = pgl.window.Window(1280, 720, resizable=True)
window.set_minimum_size(400, 400)
main_batch = pgl.graphics.Batch()
view = View(window.width // 2, window.height // 2, window, main_batch)


@window.event
def on_key_press(symbol, modifiers):
    if modifiers:
        if key.MOD_CTRL:
            if symbol == key.D:
                view.duplicate()

    else:
        # _(num) is not protected, _ is to make the name valid

        if symbol == key._1:
            if view.current_obj: view.current_obj.delete()
            view.current_obj = None
            window.set_mouse_visible(True)

        elif symbol == key._2:
            if view.current_obj: view.current_obj.delete()
            view.current_obj = Node(0, 0, view.mouse_pos[0], view.mouse_pos[1], view.scale, batch=main_batch)

        elif symbol == key._3:
            if view.current_obj: view.current_obj.delete()
            view.current_obj = Inverter(0, 0, view.mouse_pos[0], view.mouse_pos[1], view.scale, batch=main_batch)

        elif symbol == key._4:
            if view.current_obj: view.current_obj.delete()
            view.current_obj = Switch(0, 0, view.mouse_pos[0], view.mouse_pos[1], view.scale, batch=main_batch)

        elif symbol == key.DELETE:
            for obj in view.selected_objects:
                obj.delete()
                view.objects.remove(obj)
            view.selected_objects.clear()

        elif symbol == key.O:
            view.move(-view.x + window.width // 2, -view.y + window.height // 2)

        if view.current_obj:
            view.current_obj.opacity = 128
            window.set_mouse_visible(False)


@window.event
def on_mouse_leave(x, y):
    view.mouse_pos = [x, y]
    if view.current_obj:
        view.current_obj.hide()


@window.event
def on_mouse_enter(x, y):
    view.mouse_pos = [x, y]
    if view.current_obj:
        view.current_obj.show()


@window.event
def on_mouse_motion(x, y, dx, dy):
    view.mouse_pos = [x, y]

    if view.current_obj:
        try:
            x, y = view.grid_pos(x, y)
            view.current_obj.move_icon(x, y, absolute=True)
        except AttributeError:
            pass

    if view.held_copy:
        for obj in view.held_copy:
            obj.pos_x += dx
            obj.pos_y += dy

            new_x, new_y = view.grid_pos(obj.pos_x, obj.pos_y)
            obj.move_icon(new_x, new_y, absolute=True)


@window.event
def on_mouse_drag(x, y, dx, dy, button, modifiers):
    view.mouse_pos = [x, y]

    for obj in view.selected_objects:
        obj.pos_x += dx
        obj.pos_y += dy

    if view.current_obj: view.current_obj.move_icon(dx, dy)

    if button == mouse.LEFT:
        if view.held_copy:
            for obj in view.held_copy:
                obj.pos_x += dx
                obj.pos_y += dy

                new_x, new_y = view.grid_pos(obj.pos_x, obj.pos_y)
                obj.move_icon(new_x, new_y, absolute=True)

        else:
            if len(view.selected_objects) > 0:
                view.keep_selected = True
                window.set_mouse_visible(False)

            for obj in view.selected_objects:
                new_x, new_y = view.grid_pos(obj.pos_x, obj.pos_y)
                obj.move_icon(new_x, new_y, absolute=True)

    if button == mouse.RIGHT:
        view.move(dx, dy)


@window.event
def on_mouse_press(x, y, button, modifiers):
    view.mouse_pos = [x, y]

    if button == mouse.RIGHT:
        window.set_mouse_cursor(window.get_system_mouse_cursor(window.CURSOR_SIZE))

    if button == mouse.LEFT and not view.held_copy:
        obj = view.get_obj(x, y)

        if obj and not (modifiers and key.MOD_SHIFT):
            if obj not in view.selected_objects:
                view.parent_obj = obj
                view.creating_connection = True
                view.deselect_all()

        else:
            if not (modifiers and key.MOD_SHIFT): view.deselect_all()
            view.select_box = [x, y]


@window.event
def on_mouse_release(x, y, button, modifiers):
    view.mouse_pos = [x, y]

    window.set_mouse_cursor(window.get_system_mouse_cursor(window.CURSOR_DEFAULT))
    window.set_mouse_visible(True)

    if button == mouse.LEFT:
        if view.held_copy:
            view.held_copy = None

        obj = view.get_obj(x, y)

        if obj:
            if view.creating_connection and obj is not view.parent_obj: view.parent_obj.add_child(obj)
            else:
                if modifiers and key.MOD_SHIFT: view.select_multiple(x, y)
                elif not view.keep_selected: view.select(x, y)

        elif not view.creating_connection:
            if not view.keep_selected: view.deselect_all()

            if view.select_box_size(x, y) > 5:
                view.select_area(x, y)
                view.select_box = None

            elif view.current_obj:
                view.place_object(x, y)

        view.creating_connection = False
        view.select_box = None
        view.keep_selected = False


@window.event
def on_mouse_scroll(x, y, scroll_x, scroll_y):
    pass


def line(vertices, colour=(25, 25, 25)):
    """ draw a line """
    pgl.graphics.draw(2, pgl.gl.GL_LINES, ('v2i', vertices), ('c3B', colour * 2))


@window.event
def on_draw():
    window.clear()
    view.draw_grid()

    if view.creating_connection:
        line((view.parent_obj.x, view.parent_obj.y,
              view.mouse_pos[0], view.mouse_pos[1]), (100, 100, 100))

    if view.select_box_size(view.mouse_pos[0], view.mouse_pos[1]) > 5:
        # draw a box to represent the selection area
        line((view.select_box[0], view.select_box[1], view.mouse_pos[0], view.select_box[1]), (20, 255, 100))
        line((view.select_box[0], view.select_box[1], view.select_box[0], view.mouse_pos[1]), (20, 255, 100))
        line((view.select_box[0], view.mouse_pos[1], view.mouse_pos[0], view.mouse_pos[1]), (20, 255, 100))
        line((view.mouse_pos[0], view.select_box[1], view.mouse_pos[0], view.mouse_pos[1]), (20, 255, 100))

    main_batch.draw()


if __name__ == '__main__':
    pgl.app.run()
