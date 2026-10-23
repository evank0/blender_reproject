# Mesh Reprojector for Blender

This add-on reprojects the vertices of a selected mesh from one coordinate reference system (CRS) to another using `pyproj`.

Typical use cases:
- Convert WGS84 (EPSG:4326) mesh data to Web Mercator (EPSG:3857)
- Reproject a LiDAR or survey mesh from another horizontal datum into WGS84
- Align a mesh imported from XYZ point data with a georeferenced object in Blender

## Requirements

The add-on depends on `pyproj` being installed in Blender's bundled Python environment.

## Installing pyproj for Blender

You need to install the package into the Python environment used by Blender, not the system Python.

### 1. Find Blender's Python executable

On Linux, Blender often uses a Python binary located in the Blender install or a local user config path. The easiest way is to look for the executable in your Blender install directory or use the Blender Python console.

If you know the Blender executable path, you can often run:

```bash
/path/to/blender --background --python-console
```

Then in the Blender Python console, run:

```python
import sys
print(sys.executable)
```

Use that path when installing `pyproj`.

### 2. Install pyproj

Run this in a terminal:

```bash
/path/to/blender-python -m pip install pyproj
```

If Blender uses a Python executable in a bundled installation, it will usually be something like:

```bash
/usr/local/blender/5.2/python/bin/python -m pip install pyproj
```

or a user-local variant under your Blender configuration directory.

### 3. Verify the install

After installation, test from the command line:

```bash
/path/to/blender-python -c "import pyproj; print(pyproj.__version__)"
```

If that works, the add-on can use `pyproj` successfully.

## Using the add-on

1. Enable the add-on in Blender Preferences > Add-ons.
2. Select a mesh object in the 3D View.
3. Open the panel: `View3D > Sidebar > Delft3D > Mesh Reprojector`.
4. Set the source and target CRS values, for example:
   - Source: `EPSG:4326`
   - Target: `EPSG:3857`
5. Click `Reproject Selected Mesh`.

The add-on will create a new mesh object with the reprojected vertices. The original mesh can be kept or removed.
When the target CRS has an EPSG code, that code is appended to the new object's name (for example, `terrain_reprojected_EPSG_3857`).
Only the horizontal X/Y coordinates are reprojected; each vertex's Z coordinate is preserved unchanged.

## Common CRS examples

- WGS 84 geographic: `EPSG:4326`
- Web Mercator: `EPSG:3857`
- UTM zones: `EPSG:326xx` or `EPSG:327xx` depending on hemisphere

If you know the exact EPSG code for your source dataset, use that instead of the example values.

## Troubleshooting

If Blender reports that `pyproj` is not installed:
- confirm you installed it into the Blender Python environment
- use the Python executable from Blender itself
- restart Blender after installation

If the reprojected mesh appears offset:
- verify the source CRS is correct
- check whether the object transform should be included
- ensure the source data is in a horizontal CRS, not a local model-space coordinate system

## Notes

This add-on reprojects Cartesian XY coordinates using the selected CRS definitions and preserves Z values unchanged. It does not perform a vertical CRS or elevation-unit conversion. For geospatial data, the most common workflow is to transform the mesh vertices only and keep the object scale/rotation separate from the coordinate transformation.
