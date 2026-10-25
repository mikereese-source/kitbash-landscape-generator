"""Prebuild every recipe's node group into kitbash_landscape_generator/node_groups.blend, so switching
types appends a ready group instead of building ~40 s of nodes from Python. Run after any node change
(GROUP_VERSION bump); run_tests.py checks the file is current.

Run:  blender -b --factory-startup --python tests/build_library.py
"""
import os
import sys
import time

import bpy

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import kitbash_landscape_generator as lg  # noqa: E402
from kitbash_landscape_generator import nodes  # noqa: E402

lg.register()
lib = nodes.LIBRARY
if os.path.exists(lib):
    os.remove(lib)  # build fresh, never from an old copy
groups = set()
for recipe in sorted({t["recipe"] for t in lg.TYPES.values()}):
    t0 = time.time()
    ng = nodes.ensure_group(recipe)
    ng.use_fake_user = True
    groups.add(ng)
    print(f"recipe {recipe:2d}: {len(ng.nodes)} nodes, {time.time() - t0:.1f} s")
bpy.data.libraries.write(lib, groups, compress=True)
print("wrote", lib, round(os.path.getsize(lib) / 1e6, 2), "MB")
