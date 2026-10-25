# SPDX-License-Identifier: GPL-3.0-or-later
"""Saved looks ("presets"): an artist names a landscape's full look and loads it again in any project.

Stored as JSON in Blender's user config folder, outside any .blend, so a preset is there in every
file. The same JSON is meant for the three.js version later (Mike, 2026-10-25).
"""

import json
import os

import bpy

VERSION = 1
# What a preset holds besides type and style: the look, every per-type control, erosion, seed, size.
LOOK = ("height", "feature_scale", "roughness", "sharpness", "erosion_amount", "seed", "size_x", "size_y")


def path():
    folder = bpy.utils.user_resource('CONFIG', path="kitbash_landscape_generator", create=True)
    return os.path.join(folder, "presets.json")


def load_all():
    """{name: preset}. A missing or unreadable file is no presets, never an error."""
    try:
        with open(path(), encoding="utf-8") as fh:
            data = json.load(fh)
        return data.get("presets", {}) if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def _write(presets):
    tmp = path() + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump({"version": VERSION, "presets": presets}, fh, indent=1, sort_keys=True)
    os.replace(tmp, path())  # never leave a half-written file


def capture(props, control_props):
    data = {"type": props.type_key, "style": props.style_key}
    for k in LOOK + tuple(control_props):
        data[k] = getattr(props, k)
    return data


def save(name, props, control_props):
    presets = load_all()
    presets[name] = capture(props, control_props)
    _write(presets)


def delete(name):
    presets = load_all()
    presets.pop(name, None)
    _write(presets)


def rename(old, new):
    presets = load_all()
    if old in presets and new and new != old:
        presets[new] = presets.pop(old)
        _write(presets)


def apply(props, data, known_types):
    """Write a preset onto a landscape's properties (raw writes; the caller syncs once).
    Unknown keys and types are skipped, so presets from newer versions still load."""
    if data.get("type") in known_types:
        props.type_key = data["type"]
    props.style_key = data.get("style", "") or ""
    for k, v in data.items():
        if k in ("type", "style"):
            continue
        if k in props.bl_rna.properties and not props.bl_rna.properties[k].is_readonly:
            try:
                props[k] = v
            except (TypeError, ValueError):
                pass
    props.look_set = True


if __name__ == "__main__":  # self-check without Blender UI: round trip through a temp file
    import tempfile
    p = os.path.join(tempfile.mkdtemp(), "presets.json")
    globals()["path"] = lambda: p
    _write({"A": {"type": "volcano", "height": 0.3}})
    assert load_all()["A"]["height"] == 0.3
    rename("A", "B")
    assert "B" in load_all() and "A" not in load_all()
    delete("B")
    assert load_all() == {}
    print("presets self-check OK")
