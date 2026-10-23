"""Read-only image capture and the unchanged upstream host idiff expression.

This diagnostic deliberately leaves the original browser assertion failures in
place. It observes images already written before the missing-comparator guard,
then compares their bytes on the host. It does not implement browser subprocess
support and cannot turn an original browser test into a pass.
"""
from __future__ import annotations

import ast
import base64
import hashlib
import os
from pathlib import PurePosixPath
import re

SOURCE_PATH = "tests/python/bl_pyapi_blf.py"
SOURCE_SHA256 = "3a0f8e1acaa2ca2949c6b365929f04049896847e99b0759e63b1773a3871e328"
MAX_IMAGES = 256
MAX_IMAGE_BYTES = 8 * 1024 * 1024
MAX_TOTAL_BYTES = 16 * 1024 * 1024
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
RESULT_ANCHOR = "    class _Result(unittest.TextTestResult):\n"
FAILURE_ANCHOR = "        def addFailure(self, test, err):\n"


def instrument_payload(payload):
    """Add a read-only result observer; refuse an unknown adapter structure."""
    if payload.count(RESULT_ANCHOR) != 1 or payload.count(FAILURE_ANCHOR) != 1:
        raise ValueError("original unittest observer hook is absent or ambiguous")
    helper = (_CAPTURE.replace("MAX_IMAGES_LITERAL", str(MAX_IMAGES))
              .replace("MAX_IMAGE_BYTES_LITERAL", str(MAX_IMAGE_BYTES))
              .replace("MAX_TOTAL_BYTES_LITERAL", str(MAX_TOTAL_BYTES)))
    return payload.replace(RESULT_ANCHOR, helper + RESULT_ANCHOR).replace(
        FAILURE_ANCHOR, FAILURE_ANCHOR + "            _capture_font_image(test, err)\n")


def decode_image(record):
    name = record.get("filename")
    if (not isinstance(name, str) or PurePosixPath(name).name != name or
            not re.fullmatch(r"[A-Za-z0-9_.-]+_(?:buffer|vfont)_test\.png", name)):
        raise ValueError("captured image filename is not confined")
    size = record.get("bytes")
    if type(size) is not int or not 0 < size <= MAX_IMAGE_BYTES:
        raise ValueError("captured image exceeds the byte bound")
    encoded = record.get("data_b64")
    if not isinstance(encoded, str) or len(encoded) > 4 * ((MAX_IMAGE_BYTES + 2) // 3):
        raise ValueError("captured image transport exceeds the byte bound")
    data = base64.b64decode(encoded, validate=True)
    if len(data) != size or hashlib.sha256(data).hexdigest() != record.get("sha256"):
        raise ValueError("captured image checksum or size changed")
    if not data.startswith(PNG_SIGNATURE):
        raise ValueError("captured image is not a PNG")
    return data


def comparator_expression(source):
    """Extract the actual pinned source expressions instead of retyping argv."""
    text = source.decode("utf-8")
    tree = ast.parse(text)
    methods = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef) and node.name == "_compare_image"]
    if len(methods) != 1:
        raise ValueError("original image comparison method is absent or ambiguous")
    method = methods[0]
    calls = [node for node in ast.walk(method) if isinstance(node, ast.Call) and
             isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name) and
             node.func.value.id == "subprocess" and node.func.attr == "run"]
    assignments = [node for node in ast.walk(method) if isinstance(node, ast.Assign) and
                   any(isinstance(target, ast.Name) and target.id == "diff_path" for target in node.targets) and
                   isinstance(node.value, ast.Call)]
    if len(calls) != 1 or len(calls[0].args) != 1 or len(assignments) != 1:
        raise ValueError("original comparator expressions are absent or ambiguous")
    kwargs = {item.arg: ast.literal_eval(item.value) for item in calls[0].keywords}
    if kwargs != {"capture_output": True, "text": True}:
        raise ValueError("original comparator subprocess options changed")
    return {"command_source": ast.get_source_segment(text, calls[0].args[0]),
            "diff_source": ast.get_source_segment(text, assignments[0].value),
            "subprocess_options": kwargs,
            "source_sha256": hashlib.sha256(source).hexdigest()}


def original_command(expression, image, executable, diff_root):
    values = {"os": os, "OUTPUT_DIR": str(diff_root), "name_full": image["name_full"],
              "kind": image["kind"], "IDIFF_BIN": str(executable),
              "idiff_fail": image["idiff_fail"], "idiff_fail_percent": image["idiff_fail_percent"],
              "ref_path": str(image["reference_path"]), "out_path": str(image["output_path"])}
    # These expressions are taken from the checksum-bound upstream source.
    # Only filesystem roots and the executable path are remapped to host files.
    values["diff_path"] = eval(compile(expression["diff_source"], SOURCE_PATH, "eval"), {"__builtins__": {}}, values)
    command = eval(compile(expression["command_source"], SOURCE_PATH, "eval"), {"__builtins__": {}}, values)
    if not isinstance(command, list) or not all(isinstance(arg, str) for arg in command):
        raise ValueError("original comparator expression did not produce an argument vector")
    return command


_CAPTURE = r'''
    _report["font_image_capture"] = {
        "schema": 1, "scope": "read-only diagnostic before original missing-idiff assertion",
        "original_failures_preserved": True, "images": [], "errors": [], "total_bytes": 0,
        "bounds": {"files": MAX_IMAGES_LITERAL, "per_file_bytes": MAX_IMAGE_BYTES_LITERAL,
                   "total_bytes": MAX_TOTAL_BYTES_LITERAL}}
    def _capture_font_image(test, err):
        observation = _report["font_image_capture"]
        try:
            if "idiff not found, set IDIFF_BIN or install OpenImageIO" not in str(err[1]):
                return
            trace, frames = err[2], []
            while trace is not None:
                frame = trace.tb_frame
                if frame.f_code.co_name == "_compare_image" and pathlib.Path(frame.f_code.co_filename) == _main_path:
                    frames.append((frame, trace.tb_lineno))
                trace = trace.tb_next
            if len(frames) != 1:
                raise RuntimeError("missing-comparator traceback has no unique original image frame")
            frame, line = frames[0]
            values = frame.f_locals
            if frame.f_globals.get("IDIFF_BIN"):
                raise RuntimeError("original comparator was available; this observer only handles its missing guard")
            kind, name = values["kind"], values["name_full"]
            if kind not in ("buffer", "vfont"):
                raise RuntimeError("unsupported original rendering mode")
            out_path, ref_path = pathlib.Path(values["out_path"]), pathlib.Path(values["ref_path"])
            if out_path.parent != pathlib.Path(frame.f_globals["OUTPUT_DIR"]):
                raise RuntimeError("original image output is outside its temporary directory")
            if out_path.name != "{:s}_{:s}_test.png".format(name, kind):
                raise RuntimeError("original image filename changed")
            ref_relative = ref_path.relative_to(_fixture_root).as_posix()
            references = [row for row in _row.get("fixture_files", []) if row["relative_path"] == ref_relative]
            if len(references) != 1:
                raise RuntimeError("original reference is not in the pinned fixture inventory")
            reference = references[0]
            ref_data = ref_path.read_bytes()
            if len(ref_data) != reference["bytes"] or hashlib.sha256(ref_data).hexdigest() != reference["sha256"]:
                raise RuntimeError("original reference bytes changed")
            with out_path.open("rb") as stream:
                data = stream.read(MAX_IMAGE_BYTES_LITERAL + 1)
            if not data.startswith(b"\x89PNG\r\n\x1a\n") or len(data) > MAX_IMAGE_BYTES_LITERAL:
                raise RuntimeError("original output is not a bounded PNG")
            if len(observation["images"]) >= MAX_IMAGES_LITERAL or observation["total_bytes"] + len(data) > MAX_TOTAL_BYTES_LITERAL:
                raise RuntimeError("diagnostic output inventory exceeds the export bound")
            identity = _id(test)
            if any(row["case_id"] == identity or row["filename"] == out_path.name for row in observation["images"]):
                raise RuntimeError("duplicate original case or image output")
            observation["images"].append({
                "case_id": identity, "source_sha256": _row["sha256"], "original_frame_line": line,
                "name_full": name, "kind": kind, "filename": out_path.name,
                "browser_output_path": str(out_path), "browser_reference_path": str(ref_path),
                "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(),
                "data_b64": base64.b64encode(data).decode("ascii"),
                "reference": {key: reference[key] for key in ("upstream_path", "relative_path", "sha256", "bytes")},
                "idiff_fail": values["idiff_fail"], "idiff_fail_hex": float(values["idiff_fail"]).hex(),
                "idiff_fail_percent": values["idiff_fail_percent"],
                "idiff_fail_percent_hex": float(values["idiff_fail_percent"]).hex()})
            observation["total_bytes"] += len(data)
        except Exception:
            # Observer failure is reported separately and cannot replace the
            # original assertion outcome or suppress subsequent original cases.
            observation["errors"].append({"case_id": _id(test), "detail": traceback.format_exc()})
'''
