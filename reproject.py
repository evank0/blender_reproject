"""Mesh re-projection tools for Blender.

This add-on reprojects selected mesh vertices from one CRS to another,
using pyproj for the horizontal transform. Z coordinates are preserved
unchanged.
"""

import numpy as np

import bpy
from bpy.props import BoolProperty, StringProperty
from mathutils import Matrix

try:
    from pyproj import CRS, Transformer
except ImportError:  # pragma: no cover - runtime checked in Blender
    CRS = None
    Transformer = None


def _ensure_pyproj():
    if CRS is None or Transformer is None:
        raise RuntimeError(
            "pyproj is not installed in Blender's Python environment. "
            "Install it with Blender's Python: "
            "<path-to-blender-python> -m pip install pyproj"
        )


def _mesh_to_coords(obj):
    mesh = obj.data
    if mesh is None or len(mesh.vertices) == 0:
        raise ValueError(f"Object '{obj.name}' has no mesh vertices to reproject")

    coords = np.empty(len(mesh.vertices) * 3, dtype=np.float64)
    mesh.vertices.foreach_get("co", coords)
    return coords.reshape(len(mesh.vertices), 3)


def _to_world_space(coords, obj):
    if not obj.matrix_world.is_identity:
        matrix = np.asarray(obj.matrix_world, dtype=np.float64)
        ones = np.ones((len(coords), 1), dtype=np.float64)
        world = np.hstack((coords, ones)) @ matrix.T[:, :3]
        return world
    return coords.copy()


def _reproject_coords(coords, source_crs, target_crs):
    _ensure_pyproj()

    src = CRS.from_user_input(source_crs)
    dst = CRS.from_user_input(target_crs)
    transformer = Transformer.from_crs(src, dst, always_xy=True)

    x = coords[:, 0]
    y = coords[:, 1]

    new_x, new_y = transformer.transform(x, y)
    if coords.shape[1] == 2:
        return np.column_stack((new_x, new_y))

    return np.column_stack((new_x, new_y, coords[:, 2]))


def _create_mesh_object(name, source_obj, coords, include_world_transform):
    new_obj = source_obj.copy()
    new_obj.data = source_obj.data.copy()
    new_obj.name = name
    new_obj.data.name = name

    new_obj.data.vertices.foreach_set("co", coords.astype(np.float32).ravel())
    new_obj.data.update()

    if include_world_transform:
        new_obj.matrix_world = Matrix.Identity(4)
    return new_obj


class REPROJECT_OT_mesh(bpy.types.Operator):
    bl_idname = "object.reproject_mesh"
    bl_label = "Reproject Mesh"
    bl_description = "Create a new mesh object with vertices transformed from one CRS to another"
    bl_options = {'REGISTER', 'UNDO'}

    source_crs: StringProperty(
        name="Source CRS",
        description="Source CRS, such as EPSG:4326 or EPSG:3857",
        default="EPSG:4326",
    )
    target_crs: StringProperty(
        name="Target CRS",
        description="Target CRS, such as EPSG:3857 or EPSG:4326",
        default="EPSG:3857",
    )
    include_world_transform: BoolProperty(
        name="Include object transform",
        description="Project the mesh in world space before creating the new mesh. Disable to project the local vertex coordinates only.",
        default=False,
    )
    keep_original: BoolProperty(
        name="Keep original",
        description="Keep the source object in the scene and create a new projected copy.",
        default=True,
    )

    def execute(self, context):
        obj = context.active_object
        if obj is None:
            self.report({'ERROR'}, "Select a mesh object first")
            return {'CANCELLED'}

        if obj.type != 'MESH':
            self.report({'ERROR'}, f"Object '{obj.name}' is not a mesh")
            return {'CANCELLED'}

        try:
            coords = _mesh_to_coords(obj)
            if self.include_world_transform:
                coords = _to_world_space(coords, obj)

            projected = _reproject_coords(coords, self.source_crs, self.target_crs)

            new_name = f"{obj.name}_reprojected"
            new_obj = _create_mesh_object(new_name, obj, projected, self.include_world_transform)

            context.collection.objects.link(new_obj)
            context.view_layer.objects.active = new_obj
            new_obj.select_set(True)

            if not self.keep_original:
                bpy.data.objects.remove(obj, do_unlink=True)

            self.report({'INFO'}, f"Created '{new_name}' from {obj.name} ({self.source_crs} -> {self.target_crs})")
            return {'FINISHED'}
        except Exception as exc:
            self.report({'ERROR'}, f"Reprojection failed: {exc}")
            return {'CANCELLED'}


class REPROJECT_PT_panel(bpy.types.Panel):
    bl_idname = "VIEW3D_PT_reproject_mesh"
    bl_label = "Mesh Reprojector"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Delft3D'

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        layout.prop(scene, "reproject_source_crs", text="Source CRS")
        layout.prop(scene, "reproject_target_crs", text="Target CRS")
        layout.prop(scene, "reproject_include_world_transform", text="Include object transform")
        layout.prop(scene, "reproject_keep_original", text="Keep original")

        row = layout.row()
        row.operator("object.reproject_mesh", text="Reproject Selected Mesh")


classes = (
    REPROJECT_OT_mesh,
    REPROJECT_PT_panel,
)


def register_properties():
    bpy.types.Scene.reproject_source_crs = StringProperty(
        name="Source CRS",
        description="Source coordinate reference system, e.g. EPSG:4326",
        default="EPSG:4326",
    )
    bpy.types.Scene.reproject_target_crs = StringProperty(
        name="Target CRS",
        description="Target coordinate reference system, e.g. EPSG:3857",
        default="EPSG:3857",
    )
    bpy.types.Scene.reproject_include_world_transform = BoolProperty(
        name="Include object transform",
        description="Project world-space coordinates before creating the new mesh",
        default=False,
    )
    bpy.types.Scene.reproject_keep_original = BoolProperty(
        name="Keep original",
        description="Leave the original mesh in the scene",
        default=True,
    )


def unregister_properties():
    del bpy.types.Scene.reproject_source_crs
    del bpy.types.Scene.reproject_target_crs
    del bpy.types.Scene.reproject_include_world_transform
    del bpy.types.Scene.reproject_keep_original


def register():
    register_properties()
    for cls in classes:
        bpy.utils.register_class(cls)

    # Keep operator defaults synced to the scene values.
    REPROJECT_OT_mesh.source_crs = bpy.props.StringProperty(default="EPSG:4326")
    REPROJECT_OT_mesh.target_crs = bpy.props.StringProperty(default="EPSG:3857")
    REPROJECT_OT_mesh.include_world_transform = bpy.props.BoolProperty(default=False)
    REPROJECT_OT_mesh.keep_original = bpy.props.BoolProperty(default=True)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    unregister_properties()
