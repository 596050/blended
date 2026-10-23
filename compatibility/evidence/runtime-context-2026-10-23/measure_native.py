"""Read official Blender build identity and runtime options; execute no tests."""
import bpy
import json
from pathlib import Path
import sys


def value(item):
    return item.decode("utf-8", "replace") if isinstance(item, bytes) else item


fields = ("version", "version_string", "build_hash", "build_branch", "build_platform",
          "build_type", "build_cflags", "build_cxxflags", "build_linkflags", "build_system")
report = {
    "schema": 1,
    "identity": {field: value(getattr(bpy.app, field)) for field in fields},
    "build_options": {field: getattr(bpy.app.build_options, field) for field in dir(bpy.app.build_options)
                      if not field.startswith("_") and type(getattr(bpy.app.build_options, field)) is bool},
    "runtime": {"background": bpy.app.background, "python_version": sys.version, "platform": sys.platform},
    "tests_executed": 0,
    "configuration_scope": "Observed options and compiler flags in the checksum-verified official release; not a recovered full CMake cache",
}
destination = Path(sys.argv[sys.argv.index("--") + 1])
destination.write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps({"measurement_written": str(destination), "tests_executed": 0}))
