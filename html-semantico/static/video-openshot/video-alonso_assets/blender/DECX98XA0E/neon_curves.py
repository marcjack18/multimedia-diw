# Shared helpers for Blender animated title scripts.
# Keep these utilities lightweight and side-effect free.

import bpy


def ensure_rgba(color):
    """Return color with an alpha component."""
    if len(color) >= 4:
        return color
    return [color[0], color[1], color[2], 1.0]


def get_action_fcurves(action):
    """Return a collection of FCurves for this action across Blender versions."""
    if hasattr(action, "fcurves"):
        return action.fcurves

    for layer in getattr(action, "layers", []):
        for strip in getattr(layer, "strips", []):
            for bag in getattr(strip, "channelbags", []):
                curves = getattr(bag, "fcurves", None)
                if curves is not None:
                    return curves

    raise AttributeError("No fcurves found on action (unsupported Blender version?)")


def update_color_fcurves(action_name, keyframes):
    """Update RGB fcurves by keyframe index using (frame, color) pairs."""
    action = bpy.data.actions.get(action_name)
    if not action:
        return None

    fcurves = get_action_fcurves(action)
    by_index = {fc.array_index: fc for fc in fcurves}

    for point, (frame, color) in enumerate(keyframes):
        for i in range(0, 3):
            fc = by_index.get(i)
            if not fc or point >= len(fc.keyframe_points):
                continue
            coord = (frame, color[i])
            keyframe_point = fc.keyframe_points[point]
            keyframe_point.co = coord
            keyframe_point.handle_left.y = coord[1]
            keyframe_point.handle_right.y = coord[1]

    return action


def keyframe_color_socket(socket, keyframes):
    """Keyframe a 4-float color socket at provided frame/value pairs."""
    for frame, color in keyframes:
        rgba = ensure_rgba(color)
        socket.default_value = rgba
        for idx in range(4):
            socket.keyframe_insert("default_value", index=idx, frame=frame)


def keyframe_value_socket(socket, value, frames):
    """Keyframe a single-float socket at provided frames."""
    socket.default_value = value
    for frame in frames:
        socket.keyframe_insert("default_value", frame=frame)


def _get_principled_node(mat):
    nt = mat.node_tree
    return nt.nodes.get("Principled BSDF") if nt else None


def keyframe_principled(
        material_name,
        base_keyframes=None,
        emission_keyframes=None,
        emission_strength=None,
        viewport_color=None,
        specular_value=None,
        specular_color=None):
    """Keyframe principled BSDF base/emission colors and optional strength."""
    mat = bpy.data.materials.get(material_name)
    if not mat:
        return None

    if viewport_color is not None:
        mat.diffuse_color = ensure_rgba(viewport_color)

    if specular_color is not None:
        # Viewport/specular color property uses RGB only
        mat.specular_color = ensure_rgba(specular_color)[:3]

    bsdf = _get_principled_node(mat)
    if not bsdf:
        return mat

    base_sock = bsdf.inputs.get("Base Color")
    emission_sock = bsdf.inputs[27] if len(bsdf.inputs) > 27 else None
    emission_strength_sock = bsdf.inputs[28] if len(bsdf.inputs) > 28 else None
    # IOR socket (Principled input index 3)
    ior_sock = bsdf.inputs[3] if len(bsdf.inputs) > 3 else None
    # Specular tint/color socket (RGBA)
    specular_tint_sock = None
    for sock in bsdf.inputs:
        if "Specular Tint" in sock.name and sock.type == 'RGBA':
            specular_tint_sock = sock
            break
    if specular_tint_sock is None and len(bsdf.inputs) > 14 and bsdf.inputs[14].type == 'RGBA':
        specular_tint_sock = bsdf.inputs[14]

    if base_sock and base_keyframes:
        keyframe_color_socket(base_sock, base_keyframes)

    if emission_sock and emission_keyframes:
        keyframe_color_socket(emission_sock, emission_keyframes)

    if emission_strength_sock and emission_strength:
        value, frames = emission_strength
        keyframe_value_socket(emission_strength_sock, value, frames)

    if ior_sock is not None and specular_value is not None:
        ior_sock.default_value = specular_value

    if specular_tint_sock is not None and specular_color is not None:
        specular_tint_sock.default_value = ensure_rgba(specular_color)

    return mat


# OpenShot Video Editor is a program that creates, modifies, and edits video files.
#   Copyright (C) 2009  Jonathan Thomas
#
# This file is part of OpenShot Video Editor (http://launchpad.net/openshot/).
#
# OpenShot Video Editor is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenShot Video Editor is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with OpenShot Video Editor.  If not, see <http://www.gnu.org/licenses/>.


# Import Blender's python API.  This only works when the script is being
# run from the context of Blender.  Blender contains it's own version of Python
# with this library pre-installed.
import bpy
import json


def load_font(font_path):
    """ Load a new TTF font into Blender, and return the font object """
    # get the original list of fonts (before we add a new one)
    original_fonts = bpy.data.fonts.keys()

    # load new font
    bpy.ops.font.open(filepath=font_path)

    # get the new list of fonts (after we added a new one)
    for font_name in bpy.data.fonts.keys():
        if font_name not in original_fonts:
            return bpy.data.fonts[font_name]

    # no new font was added
    return None

# Debug Info:
# ./blender -b test.blend -P demo.py
# -b = background mode
# -P = run a Python script within the context of the project file


# Init all of the variables needed by this script.  Because Blender executes
# this script, OpenShot will inject a dictionary of the required parameters
# before this script is executed.
params = {
    'title': 'Oh Yeah! OpenShot!',
    'extrude': 0.1,
    'bevel_depth': 0.02,
    'spacemode': 'CENTER',
    'text_size': 1.5,
    'width': 1.0,
    'fontname': 'Bfont',

    'color': [0.8, 0.8, 0.8],
    'alpha': 1.0,

    'line1_diffuse_color': [0.8, 0.8, 0.8, 1.0],
    'line2_diffuse_color': [0.8, 0.8, 0.8, 1.0],
    'line3_diffuse_color': [0.8, 0.8, 0.8, 1.0],
    'line4_diffuse_color': [0.8, 0.8, 0.8, 1.0],

    'output_path': '/tmp/',
    'fps': 24,
    'quality': 90,
    'file_format': 'PNG',
    'color_mode': 'RGBA',
    'horizon_color': [0.57, 0.57, 0.57],
    'resolution_x': 1920,
    'resolution_y': 1080,
    'resolution_percentage': 100,
    'start_frame': 20,
    'end_frame': 25,
    'animation': True,
}


#BEGIN INJECTING PARAMS
params_json = r"""{"file_name": "TitleFileName", "title": "T\u00edtulo", "extrude": 0.1, "bevel_depth": 0.02, "fontname": "Bfont", "spacemode": "CENTER", "text_size": 1.0, "width": 1.0, "diffuse_color": [1.0, 0.6705882352941176, 0.0, 1.0], "strength": 1.0, "glare_type": "GHOSTS", "line1_diffuse_color": [0.403921568627451, 0.7372549019607844, 1.0, 1.0], "line2_diffuse_color": [0.0, 0.4117647058823529, 1.0, 1.0], "line3_diffuse_color": [0.5098039215686274, 0.7294117647058823, 1.0, 1.0], "line4_diffuse_color": [1.0, 0.8666666666666667, 0.0, 1.0], "start_frame": 1, "end_frame": 250, "length_multiplier": 1.0, "fps": 30, "resolution_x": 1280, "resolution_y": 720, "resolution_percentage": 50, "quality": 100, "file_format": "PNG", "color_mode": "RGBA", "alpha_mode": 1, "horizon_color": [0.57, 0.57, 0.57], "animation": true, "output_path": "C:\\Users\\Usuario\\.openshot_qt\\blender\\DECX98XA0E\\TitleFileName"}"""
#END INJECTING PARAMS


# The remainder of this script will modify the current Blender .blend project
# file, and adjust the settings.  The .blend file is specified in the XML file
# that defines this template in OpenShot.
# ----------------------------------------------------------------------------

# Process parameters supplied as JSON serialization
try:
    injected_params = json.loads(params_json)
    params.update(injected_params)
except NameError:
    pass

# Modify Text / Curve settings
text_object = bpy.data.curves["Text.001"]
text_object.extrude = params["extrude"]
text_object.bevel_depth = params["bevel_depth"]
text_object.body = params["title"]
text_object.align_x = params["spacemode"]
text_object.size = params["text_size"]
text_object.space_character = params["width"]

# Get font object
font = None
if params["fontname"] != "Bfont":
    # Add font so it's available to Blender
    font = load_font(params["fontname"])
else:
    # Get default font
    font = bpy.data.fonts["Bfont"]

text_object.font = font

# Change the material settings (color, alpha, etc...)
material_object = bpy.data.materials["Material.title"]
material_object.diffuse_color = params["diffuse_color"]
material_object.node_tree.nodes[1].inputs[0].default_value = params["diffuse_color"]
material_object.node_tree.nodes[1].inputs[1].default_value = params["strength"]

# Change line colors
material_object = bpy.data.materials["Material.line1"]
material_object.node_tree.nodes[1].inputs[0].default_value = params["line1_diffuse_color"]

material_object = bpy.data.materials["Material.line2"]
material_object.node_tree.nodes[1].inputs[0].default_value = params["line2_diffuse_color"]

material_object = bpy.data.materials["Material.line3"]
material_object.node_tree.nodes[1].inputs[0].default_value = params["line3_diffuse_color"]

material_object = bpy.data.materials["Material.line4"]
material_object.node_tree.nodes[1].inputs[0].default_value = params["line4_diffuse_color"]

# Change glare type
bpy.data.scenes[0].node_tree.nodes["Glare"].glare_type = params["glare_type"]

# Set the render options.  It is important that these are set
# to the same values as the current OpenShot project.  These
# params are automatically set by OpenShot
bpy.context.scene.render.filepath = params["output_path"]
bpy.context.scene.render.fps = params["fps"]
if "fps_base" in params:
    bpy.context.scene.render.fps_base = params["fps_base"]
bpy.context.scene.render.image_settings.file_format = params["file_format"]
bpy.context.scene.render.image_settings.color_mode = params["color_mode"]
bpy.context.scene.render.film_transparent = params["alpha_mode"]
bpy.context.scene.render.resolution_x = params["resolution_x"]
bpy.context.scene.render.resolution_y = params["resolution_y"]
bpy.context.scene.render.resolution_percentage = params["resolution_percentage"]

# Animation Speed (use Blender's time remapping to slow or speed up animation)
length_multiplier = round(params["length_multiplier"])  # time remapping multiplier
new_length = params["end_frame"] * length_multiplier  # new length (in frames)
bpy.context.scene.render.frame_map_old = 1
bpy.context.scene.render.frame_map_new = length_multiplier

# Set render length/position
bpy.context.scene.frame_start = params["start_frame"]
bpy.context.scene.frame_end = new_length
