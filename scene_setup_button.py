bl_info = {
    "name": "MK CT SETUP Button",
    "author": "Matt Vogel",
    "version": (1, 0),
    "blender": (2, 80, 0),
    "location": "View3D > Toolbar",
    "description": "Adds a SETUP button to the menubar",
    "warning": "",
    "wiki_url": "",
    "category": "Object"
}

import bpy


# print to the local blender console
def localPrint(data):
    for window in bpy.context.window_manager.windows:
        screen = window.screen
        for area in screen.areas:
            if area.type == 'CONSOLE':
                override = {'window': window, 'screen': screen, 'area': area}
                bpy.ops.console.scrollback_append(override, text=str(data), type="OUTPUT")

# Define a function that deletes the default cube, camera, and light
def delete_default_objects(self):
    # Delete the default cube
    bpy.data.objects['Cube'].select_set(True)
    bpy.ops.object.delete()

    # Delete the default camera
    bpy.data.objects['Camera'].select_set(True)
    bpy.ops.object.delete()

    # Delete the default light
    bpy.data.objects['Light'].select_set(True)
    bpy.ops.object.delete()



# Define a function that sets the clip end to 1m
def set_clip_distances(self, start, end):
    for a in bpy.context.screen.areas:
        if a.type == 'VIEW_3D':
            for s in a.spaces:
                if s.type == 'VIEW_3D':
                    s.clip_end = end
                    s.clip_start = start

# turn on scene statistics and face orientation
def set_viewport_overlays(self):
    for area in bpy.context.screen.areas:
        for space in area.spaces:
            localPrint(space)
            if space.type == 'VIEW_3D':
                # space.overlay.show_face_orientation = not space.overlay.show_face_orientation
                space.overlay.show_stats = not space.overlay.show_stats


class SETUPButton(bpy.types.Operator):
    bl_idname = "object.setup_button"
    bl_label = "SETUP"

    def execute(self, context):

        # Call the function that sets the clip start and end
        set_clip_distances(self, .01, 1000000)
        
        # set up the viewer
        set_viewport_overlays(self)

        try:
            # Call the function that deletes the default cube, camera, and light
            delete_default_objects(self)
        except KeyError:
            pass

        return {'FINISHED'}


def setup_button(self, context):
    self.layout.operator(SETUPButton.bl_idname)


def register():
    bpy.utils.register_class(SETUPButton)
    bpy.types.VIEW3D_MT_editor_menus.append(setup_button)


def unregister():
    bpy.utils.unregister_class(SETUPButton)
    bpy.types.VIEW3D_MT_editor_menus.remove(setup_button)


if __name__ == "__main__":
    register()
