"""Blender mesh reprojection add-on."""

bl_info = {
    "name": "Mesh Reprojector",
    "author": "Evan Kennedy",
    "version": (1, 0, 1),
    "blender": (5, 0, 0),
    "location": "View3D > Sidebar > Delft3D",
    "description": "Reproject a selected mesh between coordinate reference systems",
    "category": "Object",
}

import bpy

from . import reproject


def register():
    reproject.register()


def unregister():
    reproject.unregister()


if __name__ == "__main__":
    register()
