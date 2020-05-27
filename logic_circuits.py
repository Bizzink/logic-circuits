import pyglet as pgl
from pyglet.window import mouse, key
from Node import Node
from Inverter import Inverter
from Switch import Switch
from View import View
# from Subcircuit import Subcircuit

window = pgl.window.Window(1280, 720, resizable=True)
window.set_minimum_size(400, 400)
view = View(window)


@window.event
def on_key_press(symbol, modifiers):
    if modifiers:
        if key.MOD_CTRL:
            if symbol == key.D:
                view.duplicate()

            # if symbol == key.G:
            #     subcircuit = Subcircuit(view)
            #     view.objects.append(subcircuit)
            #     view.held_copy = [subcircuit]

    else:
        # object selector
        # _(num) is not protected, _ is to make the name valid
        if symbol == key._1: view.set_object(None)
        elif symbol == key._2: view.set_object(Node)
        elif symbol == key._3: view.set_object(Inverter)
        elif symbol == key._4: view.set_object(Switch)

        # delete selected objects++
        elif symbol == key.DELETE:
            for obj in view.selected_objects:
                obj.delete()
                view.objects.remove(obj)
            view.selected_objects.clear()

        # reset view to origin
        elif symbol == key.O: view.move(-view.x, -view.y)


@window.event
def on_mouse_leave(x, y):
    view.mouse.pos(x, y)
    if view.current_obj:
        view.current_obj.visible = False


@window.event
def on_mouse_enter(x, y):
    view.mouse.pos(x, y)
    if view.current_obj:
        view.current_obj.visible = True


@window.event
def on_mouse_motion(x, y, dx, dy):
    view.mouse.pos(x, y)

    if view.held_copy:
        for obj in view.held_copy:
            obj.move_pos(dx // view.get_scale(), dy // view.get_scale())
            x, y = view.screen_pos(obj.pos_x, obj.pos_y)
            x, y = view.grid_pos(x, y)
            x, y = view.world_pos(x, y)
            obj.move_icon(x, y, absolute=True)


@window.event
def on_mouse_drag(x, y, dx, dy, button, modifiers):
    view.mouse.pos(x, y)

    if button == mouse.LEFT:
        if view.held_copy:
            for obj in view.held_copy:
                obj.move_pos(dx // view.get_scale(), dy // view.get_scale())
                x, y = view.screen_pos(obj.pos_x, obj.pos_y)
                x, y = view.grid_pos(x, y)
                x, y = view.world_pos(x, y)
                obj.move_icon(x, y, absolute=True)

        else:
            if len(view.selected_objects) > 0:
                view.keep_selected = True
                window.set_mouse_visible(False)

            for obj in view.selected_objects:
                obj.move_pos(dx // view.get_scale(), dy // view.get_scale())
                x, y = view.screen_pos(obj.pos_x, obj.pos_y)
                x, y = view.grid_pos(x, y)
                x, y = view.world_pos(x, y)
                obj.move_icon(x, y, absolute=True)

    if button == mouse.RIGHT:
        view.move(dx, dy)


@window.event
def on_mouse_press(x, y, button, modifiers):
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
            x, y = view.world_pos(x, y)
            view.select_box.pos(x, y)


@window.event
def on_mouse_release(x, y, button, modifiers):
    window.set_mouse_cursor(window.get_system_mouse_cursor(window.CURSOR_DEFAULT))
    if not view.current_obj: window.set_mouse_visible(True)

    if button == mouse.LEFT:
        if view.held_copy:
            for obj in view.held_copy:
                new_x, new_y = view.screen_pos(obj.x, obj.y)
                new_x, new_y = view.grid_pos(new_x, new_y)
                new_x, new_y = view.world_pos(new_x, new_y)
                obj.move_icon(new_x, new_y, absolute=True)
                obj.move_pos(to_icon=True)

            view.held_copy = None

        elif view.selected_objects:
            for obj in view.selected_objects:
                new_x, new_y = view.screen_pos(obj.x, obj.y)
                new_x, new_y = view.grid_pos(new_x, new_y)
                new_x, new_y = view.world_pos(new_x, new_y)
                obj.move_icon(new_x, new_y, absolute=True)
                obj.move_pos(to_icon=True)

        obj = view.get_obj(x, y)

        if obj:
            if view.creating_connection and obj is not view.parent_obj: view.parent_obj.add_child(obj)
            else:
                if modifiers and key.MOD_SHIFT: view.select_multiple(obj = obj)
                elif not view.keep_selected: view.select(x, y)

        elif not view.creating_connection:
            if not view.keep_selected: view.deselect_all()

            if view.select_box_size(x, y) > 25:
                view.select_area(x, y)
                view.select_box.pos(None, None)

            elif view.current_obj:
                view.place_object(x, y)

        view.creating_connection = False
        view.select_box.pos(None, None)
        view.keep_selected = False


@window.event
def on_mouse_scroll(x, y, scroll_x, scroll_y):
    view.scale(scroll_y)


@window.event
def on_draw():
    window.clear()
    view.draw()


if __name__ == '__main__':
    pgl.app.run()
