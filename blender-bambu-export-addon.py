import bpy
import subprocess
import os
import tempfile
from bpy.types import Operator, Panel
from bpy.props import FloatVectorProperty
import bmesh

bl_info = {
    "name": "Export to Bambu Studio",
    "author": "Your Name",
    "version": (1, 1),
    "blender": (4, 2, 0),
    "location": "File > Export > Bambu Studio (.stl), Toolbar",
    "description": "Export selected object as STL and open in Bambu Studio, plus additional utilities",
    "category": "Import-Export",
}

# Function to log messages
def log(message):
    print(message)  # This will print to the System Console

# Function to export STL
def export_stl(filepath):
    try:
        if not bpy.ops.export_mesh.stl.poll():
            raise Exception("STL export operator is not available. Ensure the STL add-on is enabled.")
        bpy.ops.export_mesh.stl(filepath=filepath, use_selection=True)
        log(f"Successfully exported to {filepath}")
    except Exception as e:
        log(f"Error during export: {str(e)}")
        raise

# Function to open file in Bambu Studio
def open_file_with_bambu_studio(file_path):
    try:
        app_path = "/Applications/BambuStudio.app"
        if not os.path.exists(app_path):
            raise Exception(f"Bambu Studio not found at {app_path}")
        subprocess.Popen(["open", "-a", app_path, file_path])
        log(f"Opened {file_path} in Bambu Studio")
    except Exception as e:
        log(f"Error opening file in Bambu Studio: {str(e)}")
        raise

# Operator for exporting and opening in Bambu Studio
class ExportSTLAndOpenBambu(Operator):
    bl_idname = "export.stl_and_open_bambu"
    bl_label = "Export STL and Open in Bambu Studio"

    def execute(self, context):
        try:
            if not bpy.context.selected_objects:
                raise Exception("No object selected. Please select an object to export.")

            # Use a temporary file path
            temp_dir = tempfile.gettempdir()
            export_path = os.path.join(temp_dir, "bambu_export.stl")

            export_stl(export_path)
            open_file_with_bambu_studio(export_path)
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, str(e))
            return {'CANCELLED'}

# Operator for creating build volume representation
class CreateBuildVolume(Operator):
    bl_idname = "object.create_build_volume"
    bl_label = "Create P1S Build Volume"

    def create_wireframe_cube(self, context):
        mesh = bpy.data.meshes.new("P1S Build Volume")
        cube = bpy.data.objects.new("P1S Build Volume", mesh)
        
        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=1)
        bm.to_mesh(mesh)
        bm.free()
        
        cube.scale = (256, 256, 256)  # 256mm = 0.256m in each dimension
        cube.location = (0, 0, 128)  # Center the bottom at 0,0,0
        cube.display_type = 'WIRE'
        
        context.collection.objects.link(cube)
        return cube

    def execute(self, context):
        cube = self.create_wireframe_cube(context)
        self.report({'INFO'}, "P1S Build Volume created")
        return {'FINISHED'}


class BakeVertexColors(Operator):
    bl_idname = "object.bake_vertex_colors"
    bl_label = "Bake Vertex Colors"
    
    color: FloatVectorProperty(
        name="Color",
        subtype='COLOR',
        default=(1.0, 1.0, 1.0),
        min=0.0, max=1.0,
        description="Color to bake to vertices"
    )

    def execute(self, context):
        obj = context.active_object
        if obj and obj.type == 'MESH':
            mesh = obj.data
            if not mesh.vertex_colors:
                mesh.vertex_colors.new()
            color_layer = mesh.vertex_colors.active
            
            # Assign color to all vertices
            for poly in mesh.polygons:
                for loop_index in poly.loop_indices:
                    color_layer.data[loop_index].color = (*self.color, 1.0)
            
            self.report({'INFO'}, "Vertex colors baked")
        else:
            self.report({'ERROR'}, "No mesh object selected")
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

# Operator for removing vertex colors
class RemoveVertexColors(Operator):
    bl_idname = "object.remove_vertex_colors"
    bl_label = "Remove Vertex Colors"

    def execute(self, context):
        obj = context.active_object
        if obj and obj.type == 'MESH':
            mesh = obj.data
            if mesh.vertex_colors:
                for vcol in mesh.vertex_colors:
                    mesh.vertex_colors.remove(vcol)
            self.report({'INFO'}, "Vertex colors removed")
        else:
            self.report({'ERROR'}, "No mesh object selected")
        return {'FINISHED'}
    
# Panel for the toolbar button
class BambuStudioPanel(Panel):
    bl_label = "Bambu Studio Tools"
    bl_idname = "OBJECT_PT_bambu_studio"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Bambu Studio"

    def draw(self, context):
        layout = self.layout
        layout.operator("export.stl_and_open_bambu", text="Export to Bambu")
        layout.operator("object.create_build_volume", text="Create P1S Build Volume")
        layout.operator("object.bake_vertex_colors", text="Bake Vertex Colors")
        layout.operator("object.remove_vertex_colors", text="Remove Vertex Colors")

# Function to add menu item
def menu_func_export(self, context):
    self.layout.operator(ExportSTLAndOpenBambu.bl_idname, text="Bambu Studio (.stl)")

# Register and unregister functions
def register():
    bpy.utils.register_class(ExportSTLAndOpenBambu)
    bpy.utils.register_class(CreateBuildVolume)
    bpy.utils.register_class(BakeVertexColors)
    bpy.utils.register_class(RemoveVertexColors)
    bpy.utils.register_class(BambuStudioPanel)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)

def unregister():
    bpy.utils.unregister_class(ExportSTLAndOpenBambu)
    bpy.utils.unregister_class(CreateBuildVolume)
    bpy.utils.unregister_class(BakeVertexColors)
    bpy.utils.unregister_class(RemoveVertexColors)
    bpy.utils.unregister_class(BambuStudioPanel)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)

if __name__ == "__main__":
    register()