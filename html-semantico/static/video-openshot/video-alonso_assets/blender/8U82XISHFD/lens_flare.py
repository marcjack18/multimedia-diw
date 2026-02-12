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


def _safe_rgba(value):
    """Coerce color-like input to RGBA without assuming sequence length."""
    try:
        return ensure_rgba(value)
    except Exception:
        try:
            v = float(value)
            return [v, v, v, 1.0]
        except Exception:
            return [1.0, 1.0, 1.0, 1.0]

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
params_json = r"""{"file_name": "TitleFileName", "Alongtimeago": "A long time ago in a video\neditor far, far away...", "TitleSpaceMovie": "open\nshot", "Episode": "Episode XXIII", "EpisodeTitle": "A NEW OPENSHOT", "MainText": "Es una \u00e9poca de dominio en la F\u00f3rmula 1. Mientras las escuder\u00edas imperiales imponen su ley con monoplazas invencibles, un veterano guerrero asturiano se niega a rendirse.\n\nArmado \u00fanicamente con su talento y unas manos que desaf\u00edan el paso del tiempo, Fernando Alonso lucha contra los l\u00edmites de la f\u00edsica, rozando los muros y buscando mil\u00e9simas donde otros solo ven peligro.\n\nLa \"Misi\u00f3n 33\" est\u00e1 m\u00e1s viva que nunca en la noche del desierto. Prep\u00e1rense para una clase magistral de pilotaje... os dejamos con su vuelta de clasificaciones en jeddah 2023.", "start_frame": 1, "end_frame": 250, "length_multiplier": 1.0, "start_x": 3.8, "start_y": 4.13, "start_z": 2.65, "end_x": -4.6, "end_y": 4.13, "end_z": 3.21, "alpha": 1.0, "diffuse_color": [1.0, 1.0, 1.0, 1.0], "strength": 0.75, "glare1_type": "Ghosts", "glare1_streaks": 4.0, "glare1_color": 0.25, "glare1_angle": 0.0, "glare2_type": "Streaks", "glare2_streaks": 4.0, "glare2_color": 0.25, "glare2_angle": 0.0, "fps": 30, "resolution_x": 1280, "resolution_y": 720, "resolution_percentage": 50, "quality": 100, "file_format": "PNG", "color_mode": "RGBA", "alpha_mode": 1, "horizon_color": [0.57, 0.57, 0.57], "animation": true, "output_path": "C:\\Users\\Usuario\\.openshot_qt\\blender\\8U82XISHFD\\TitleFileName"}"""
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

# Modify the Location of the Wand
sphere_object = bpy.data.objects["Sphere"]
sphere_object.location = [params["start_x"], params["start_y"], params["start_z"]]

# Modify the Start and End keyframes (Blender 5-safe)
action = bpy.data.actions.get("SphereAction")
if action:
    try:
        fcurves = list(get_action_fcurves(action))
    except Exception:
        fcurves = list(getattr(action, "fcurves", []))

    by_index = {fc.array_index: fc for fc in fcurves}

    fc_x = by_index.get(0) if by_index else (fcurves[0] if len(fcurves) > 0 else None)
    fc_y = by_index.get(1) if by_index else (fcurves[1] if len(fcurves) > 1 else None)
    fc_z = by_index.get(2) if by_index else (fcurves[2] if len(fcurves) > 2 else None)

    def _set_kp(fc, idx, frame, value):
        if fc and len(fc.keyframe_points) > idx:
            kp = fc.keyframe_points[idx]
            kp.co = (frame, value)
            kp.handle_left.y = value
            kp.handle_right.y = value

    _set_kp(fc_x, 0, 1.0, params["start_x"])
    _set_kp(fc_y, 0, 1.0, params["start_y"])
    _set_kp(fc_z, 0, 1.0, params["start_z"])
    _set_kp(fc_x, 1, 300.0, params["end_x"])
    _set_kp(fc_y, 1, 300.0, params["end_y"])
    _set_kp(fc_z, 1, 300.0, params["end_z"])

# Change the material settings (color, alpha, etc...)
material_object = bpy.data.materials.get("Material.001")
if material_object and material_object.node_tree:
    principled = material_object.node_tree.nodes.get("Principled BSDF")
    if principled:
        principled.inputs[0].default_value = _safe_rgba(params["diffuse_color"])
        if len(principled.inputs) > 26:
            principled.inputs[26].default_value = _safe_rgba(params["diffuse_color"])  # Emission color
        strength_value = params["strength"]
        if len(principled.inputs) > 27:
            principled.inputs[27].default_value = (strength_value, strength_value, strength_value, 1.0)
        alpha_input = principled.inputs.get("Alpha")
        if alpha_input:
            alpha_input.default_value = params["alpha"]

# Change Composite Node settings
glare_node = bpy.data.node_groups["Compositing Nodetree"].nodes["Glare"]
glare_node.inputs[9].default_value = params["diffuse_color"]
glare_node.inputs[1].default_value = params["glare1_type"]
glare_node.inputs[11].default_value = round(params["glare1_streaks"])
glare_node.inputs[12].default_value = params["glare1_angle"]

glare_node = bpy.data.node_groups["Compositing Nodetree"].nodes["Glare.001"]
glare_node.inputs[9].default_value = params["diffuse_color"]
glare_node.inputs[1].default_value = params["glare2_type"]
glare_node.inputs[11].default_value = round(params["glare2_streaks"])
glare_node.inputs[12].default_value = params["glare2_angle"]

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
