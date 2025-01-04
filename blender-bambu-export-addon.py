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
    "version": (1, 2),
    "blender": (4, 2, 0),
    "location": "File > Export > Bambu Studio (.stl), Toolbar",
    "description": "Export to Bambu Studio with options for merged or separate STLs",
    "category": "Import-Export",
}

def log(message):
    print(message)

def export_stl(filepath):
    try:
        if not bpy.ops.export_mesh.stl.poll():
            raise Exception("STL export operator is not available. Ensure the STL add-on is enabled.")
        bpy.ops.export_mesh.stl(filepath=filepath, use_selection=True)
        log(f"Successfully exported to {filepath}")
    except Exception as e:
        log(f"Error during export: {str(e)}")
        raise

def export_stl_single(obj, filepath):
    try:
        # Deselect all objects
        bpy.ops.object.select_all(action='DESELECT')
        
        # Select only the current object
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        
        # Export only this object
        bpy.ops.export_mesh.stl(filepath=filepath, use_selection=True)
        log(f"Successfully exported {obj.name} to {filepath}")
        
        # Deselect the object
        obj.select_set(False)
    except Exception as e:
        log(f"Error during export of {obj.name}: {str(e)}")
        raise

def open_file_with_bambu_studio(file_paths):
    if isinstance(file_paths, str):
        file_paths = [file_paths]
        
    try:
        app_path = "/Applications/BambuStudio.app"
        if not os.path.exists(app_path):
            raise Exception(f"Bambu Studio not found at {app_path}")
        
        # Open all files in Bambu Studio
        for file_path in file_paths:
            subprocess.Popen(["open", "-a", app_path, file_path])
            log(f"Opened {file_path} in Bambu Studio")
    except Exception as e:
        log(f"Error opening files in Bambu Studio: {str(e)}")
        raise

class ExportSTLAndOpenBambu(Operator):
    bl_idname = "export.stl_and_open_bambu"
    bl_label = "Export Merged STL to Bambu"
    
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

class ExportPartsSTLAndOpenBambu(Operator):
    bl_idname = "export.parts_stl_and_open_bambu"
    bl_label = "Export Parts as STL to Bambu"

    def execute(self, context):
        try:
            selected_objects = [obj for obj in bpy.context.selected_objects if obj.type == 'MESH']
            
            if not selected_objects:
                raise Exception("No mesh objects selected. Please select objects to export.")

            # Create temporary directory for multiple files
            temp_dir = tempfile.mkdtemp()
            export_paths = []

            # Export each selected object separately
            for obj in selected_objects:
                file_name = f"{obj.name}.stl"
                export_path = os.path.join(temp_dir, file_name)
                export_stl_single(obj, export_path)
                export_paths.append(export_path)

            # Open all exported files in Bambu Studio
            open_file_with_bambu_studio(export_paths)
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, str(e))
            return {'CANCELLED'}

# [Previous operators remain the same]
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
            
            for poly in mesh.polygons:
                for loop_index in poly.loop_indices:
                    color_layer.data[loop_index].color = (*self.color, 1.0)
            
            self.report({'INFO'}, "Vertex colors baked")
        else:
            self.report({'ERROR'}, "No mesh object selected")
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

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
    
class BambuStudioPanel(Panel):
    bl_label = "Bambu Studio Tools"
    bl_idname = "OBJECT_PT_bambu_studio"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Bambu Studio"

    def draw(self, context):
        layout = self.layout
        
        # Export section
        box = layout.box()
        box.label(text="Export Options:")
        box.operator("export.stl_and_open_bambu", text="Export Merged to Bambu")
        box.operator("export.parts_stl_and_open_bambu", text="Export Parts to Bambu")
        
        # Other tools section
        box = layout.box()
        box.label(text="Utilities:")
        box.operator("object.create_build_volume", text="Create P1S Build Volume")
        box.operator("object.bake_vertex_colors", text="Bake Vertex Colors")
        box.operator("object.remove_vertex_colors", text="Remove Vertex Colors")

def menu_func_export(self, context):
    self.layout.operator(ExportSTLAndOpenBambu.bl_idname, text="Bambu Studio (.stl)")
    self.layout.operator(ExportPartsSTLAndOpenBambu.bl_idname, text="Bambu Studio - Separate Parts (.stl)")

def register():
    bpy.utils.register_class(ExportSTLAndOpenBambu)
    bpy.utils.register_class(ExportPartsSTLAndOpenBambu)
    bpy.utils.register_class(CreateBuildVolume)
    bpy.utils.register_class(BakeVertexColors)
    bpy.utils.register_class(RemoveVertexColors)
    bpy.utils.register_class(BambuStudioPanel)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)

def unregister():
    bpy.utils.unregister_class(ExportSTLAndOpenBambu)
    bpy.utils.unregister_class(ExportPartsSTLAndOpenBambu)
    bpy.utils.unregister_class(CreateBuildVolume)
    bpy.utils.unregister_class(BakeVertexColors)
    bpy.utils.unregister_class(RemoveVertexColors)
    bpy.utils.unregister_class(BambuStudioPanel)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)

if __name__ == "__main__":
    register()