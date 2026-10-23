# SPDX-FileCopyrightText: 2011-2022 Blender Authors
# SPDX-FileCopyrightText: 2025 Blender Authors
# SPDX-FileCopyrightText: 2026 Blended contributors
#
# SPDX-License-Identifier: Apache-2.0
"""Diagnostic observations for two unmodified upstream-suite failures.

Execute these exact bytes inside either native Blender or the browser port.
This payload does not modify acceptance tests, patch mathutils/BMesh, change
tolerances, update reference data, or decide whether a facet has parity.

The input vectors and complex screw construction are adapted from:
  blender/blender@fbe6228777e7d9afefcd61a413844e790ae75db7
  tests/python/bl_pyapi_mathutils.py (blob 3f152413bd28842706d83957d0ff3690788c3ae7)
  tests/python/bl_pyapi_bmesh.py (blob 663e8cd1b07bff9dbd8468edd346048e3179f11f)
Both upstream test sources carry Apache-2.0 notices.

Protocol: print one BLENDED_NUMERIC_DIAGNOSTICS: prefixed JSON object. Case IDs
and original inputs are stable across engines. Float encodings are big-endian
IEEE-754 hexadecimal. JSON contains no NaN or Infinity numeric literals.
"""

from __future__ import annotations

import hashlib
import json
import math
import struct
import sys
import traceback


MARKER = "BLENDED_NUMERIC_DIAGNOSTICS:"
UPSTREAM_COMMIT = "fbe6228777e7d9afefcd61a413844e790ae75db7"

_BASE_VECTORS = (
    (1.0, 0.0, 0.0),
    (0.0, 1.0, 0.0),
    (0.0, 0.0, 1.0),
    (1.0, 1.0, 1.0),
    (0.33783, 0.715698, -0.611206),
    (-0.944031, -0.326599, -0.045624),
    (-0.101074, -0.416443, -0.903503),
    (0.799286, 0.49411, -0.341949),
    (-0.854645, 0.518036, 0.033936),
    (0.42514, -0.437866, -0.792114),
    (-0.358948, 0.597046, 0.717377),
    (-0.985413, 0.144714, 0.089294),
)
_SCALES = tuple(
    size * sign
    for size in (0.0001, 0.1, 1.0, 10.0, 1000.0, 100000.0)
    for sign in (1.0, -1.0)
)
_VECTOR_DATA = sum(
    (tuple(tuple(a * scale for a in v) for v in _BASE_VECTORS) for scale in _SCALES),
    (),
) + ((0.0, 0.0, 0.0),)


def _json_bytes(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def _digest(value):
    return hashlib.sha256(_json_bytes(value)).hexdigest()


def _number(value):
    value = float(value)
    if math.isnan(value):
        return "NaN"
    if math.isinf(value):
        return "Infinity" if value > 0 else "-Infinity"
    return value


def _float(value):
    value = float(value)
    try:
        bits32 = struct.pack(">f", value).hex()
    except OverflowError:
        bits32 = None
    return {
        "value": _number(value),
        "f32_bits_be": bits32,
        "f64_bits_be": struct.pack(">d", value).hex(),
        "python_hex": value.hex(),
    }


def _vector(value):
    values = tuple(float(x) for x in value)
    return {
        "values": [_number(x) for x in values],
        "f32_bits_be": [struct.pack(">f", x).hex() for x in values],
        "f64_bits_be": [struct.pack(">d", x).hex() for x in values],
    }


def _matrix(value):
    return [_vector(row) for row in value]


def _text(value):
    return value.decode("utf-8", "replace") if isinstance(value, bytes) else str(value)


def _error():
    exc = sys.exc_info()[1]
    return {"type": type(exc).__name__, "message": str(exc), "traceback": traceback.format_exc()}


def _would_fail_almost_equal(actual, expected, places):
    """Observe unittest's numeric rule, without running/modifying an assertion."""
    if actual == expected:
        return False
    return round(abs(actual - expected), places) != 0


def _vector_inputs(index, components):
    is_zero = index == len(_VECTOR_DATA) - 1
    return {
        "upstream_index": index,
        "base_index": None if is_zero else index % len(_BASE_VECTORS),
        "scale": None if is_zero else _SCALES[index // len(_BASE_VECTORS)],
        "components": list(components),
        "upstream_expected_angle": math.pi / 2.0,
        "upstream_assert_almost_equal_places": 7,
    }


def _observe_vector(index, components):
    from mathutils import Vector

    result = {"id": "orthogonal/%04d" % index, "inputs": _vector_inputs(index, components)}
    try:
        v = Vector(components)
        result["input_vector"] = _vector(v)
        result["mathutils_length_squared"] = _float(v.length_squared)
        if v.length_squared == 0.0:
            result["diagnostic_status"] = "skipped_zero"
            result["reason"] = "The original test does not call angle for a zero-length vector."
            return result

        ortho = v.orthogonal()
        angle = v.angle(ortho)
        av, bv = tuple(v), tuple(ortho)
        dot64 = math.fsum(a * b for a, b in zip(av, bv))
        norm_a64 = math.sqrt(math.fsum(a * a for a in av))
        norm_b64 = math.sqrt(math.fsum(b * b for b in bv))
        normalized_a64 = tuple(a / norm_a64 for a in av)
        normalized_b64 = tuple(b / norm_b64 for b in bv)
        cosine64 = dot64 / (norm_a64 * norm_b64)
        normalized_dot64 = math.fsum(a * b for a, b in zip(normalized_a64, normalized_b64))
        vn, on = v.normalized(), ortho.normalized()
        target = math.pi / 2.0
        result.update({
            "diagnostic_status": "complete",
            "orthogonal_vector": _vector(ortho),
            "mathutils_dot": _float(v.dot(ortho)),
            "mathutils_angle": _float(angle),
            "angle_error_from_pi_over_two": _float(angle - target),
            "would_fail_original_assertion": _would_fail_almost_equal(angle, target, 7),
            "mathutils_normalized_input": _vector(vn),
            "mathutils_normalized_orthogonal": _vector(on),
            "mathutils_normalized_dot": _float(vn.dot(on)),
            "python_double_dot_from_stored_f32": _float(dot64),
            "python_double_input_norm": _float(norm_a64),
            "python_double_orthogonal_norm": _float(norm_b64),
            "python_double_normalized_input": _vector(normalized_a64),
            "python_double_normalized_orthogonal": _vector(normalized_b64),
            "python_double_cosine": _float(cosine64),
            "python_double_normalized_dot": _float(normalized_dot64),
            "python_double_acos": _float(math.acos(max(-1.0, min(1.0, cosine64)))),
        })
    except Exception:
        result.update({"diagnostic_status": "error", "error": _error()})
    return result


def _screw_inputs(do_dupli):
    return {
        "test": "TestBMeshOperators.test_spin_screw_complex",
        "use_duplicate": do_dupli,
        "space_translation": [10.0, 0.0, 0.0],
        "space_rotation_degrees": 90.0,
        "space_rotation_axis": [1.0, 1.0, 1.0],
        "space_uniform_scale": 2.0,
        "initial_vertices": [
            [11.0, 0.0, 0.0], [11.0, 0.0, 1.0], [11.0, 0.0, 2.0],
            [11.0, 0.0, 3.0], [12.0, 0.0, 3.0], [12.0, 0.0, 4.0], [11.0, 0.0, 4.0],
        ],
        "initial_edges": [[1, 2]],
        "initial_faces": [[3, 4, 5, 6]],
        "cent": [0.0, 0.0, 0.0],
        "axis": [0.0, 0.0, 1.0],
        "angle_degrees": 360.0,
        "steps": 6,
        "dvec": [0.0, 0.0, 0.5],
        "upstream_expected_counts": [49, 35, 7] if do_dupli else [49, 77, 32],
        "upstream_expected_area": 7.0 if do_dupli else 297.830433,
        "upstream_expected_length": 35.0 if do_dupli else 651.346448,
        "upstream_assert_almost_equal_places": 4,
    }


def _canonical_loop(indices):
    # Preserve winding while removing an arbitrary starting corner.
    values = tuple(indices)
    return min(values[i:] + values[:i] for i in range(len(values))) if values else ()


def _observe_screw(do_dupli):
    import bmesh
    from mathutils import Matrix, Vector

    result = {
        "id": "complex_screw/duplicate_%s" % str(do_dupli).lower(),
        "inputs": _screw_inputs(do_dupli),
    }
    bm = None
    try:
        # Same construction and expression order as the pinned upstream test.
        rotation = Matrix.Rotation(math.radians(90.0), 4, Vector((1.0, 1.0, 1.0)))
        space = Matrix.Translation((10.0, 0.0, 0.0)) @ rotation @ Matrix.Scale(2.0, 4)
        result["rotation_matrix"] = _matrix(rotation)
        result["space_matrix"] = _matrix(space)
        result["inverse_space_matrix"] = _matrix(space.inverted())
        result["normalized_rotation_axis"] = _vector(Vector((1.0, 1.0, 1.0)).normalized())
        result["rotation_radians"] = _float(math.radians(90.0))
        result["spin_radians"] = _float(math.radians(360.0))

        bm = bmesh.new()
        seeds = [bm.verts.new((11.0, 0.0, 0.0))]
        edge_vertices = [bm.verts.new(co) for co in ((11.0, 0.0, 1.0), (11.0, 0.0, 2.0))]
        seeds.extend(edge_vertices)
        bm.edges.new(edge_vertices)
        face_vertices = [bm.verts.new(co) for co in (
            (11.0, 0.0, 3.0), (12.0, 0.0, 3.0), (12.0, 0.0, 4.0), (11.0, 0.0, 4.0),
        )]
        seeds.extend(face_vertices)
        bm.faces.new(face_vertices)
        bmesh.ops.spin(
            bm,
            geom=bm.verts[:] + bm.edges[:] + bm.faces[:],
            cent=(0.0, 0.0, 0.0),
            axis=(0.0, 0.0, 1.0),
            space=space,
            angle=math.radians(360.0),
            steps=6,
            dvec=(0.0, 0.0, 0.5),
            use_duplicate=do_dupli,
        )
        bm.verts.ensure_lookup_table()
        bm.edges.ensure_lookup_table()
        bm.faces.ensure_lookup_table()
        bm.verts.index_update()
        bm.edges.index_update()
        bm.faces.index_update()

        vertices = [{"id": "vertex/%04d" % v.index, "index": v.index, "co": _vector(v.co)} for v in bm.verts]
        edges = []
        for edge in bm.edges:
            a, b = tuple(edge.verts[0].co), tuple(edge.verts[1].co)
            length64 = math.sqrt(math.fsum((x - y) ** 2 for x, y in zip(a, b)))
            edges.append({
                "id": "edge/%04d" % edge.index,
                "index": edge.index,
                "vertex_indices": [v.index for v in edge.verts],
                "length": _float(edge.calc_length()),
                "python_double_length_from_stored_f32": _float(length64),
                "mathutils_edge_delta": _vector(edge.verts[1].co - edge.verts[0].co),
            })
        faces = [{
            "id": "face/%04d" % face.index,
            "index": face.index,
            "vertex_indices": [v.index for v in face.verts],
            "area": _float(face.calc_area()),
        } for face in bm.faces]
        # These sums preserve the original test's element iteration and Python sum.
        areas = [face.calc_area() for face in bm.faces]
        lengths = [edge.calc_length() for edge in bm.edges]
        total_area, total_length = sum(areas), sum(lengths)
        coords = sorted(set(tuple(v.co) for v in bm.verts))
        topology = {
            "vertex_count": len(vertices),
            "original_seed_vertex_indices": [v.index for v in seeds],
            "edges_in_iteration_order": [sorted(e["vertex_indices"]) for e in edges],
            "faces_in_iteration_order": [list(_canonical_loop(f["vertex_indices"])) for f in faces],
        }
        expected = result["inputs"]
        result.update({
            "diagnostic_status": "complete",
            "counts": [len(bm.verts), len(bm.edges), len(bm.faces)],
            "vertices": vertices,
            "edges": edges,
            "faces": faces,
            "topology": topology,
            "topology_sha256": _digest(topology),
            "index_pairing_policy": "BMesh iteration indices after spin; pair indices only when topology_sha256 and original seed anchors match. No geometry is changed by index_update.",
            "unique_coordinates_sorted": [_vector(co) for co in coords],
            "total_area_original_sum": _float(total_area),
            "total_length_original_sum": _float(total_length),
            "total_area_fsum": _float(math.fsum(areas)),
            "total_length_fsum": _float(math.fsum(lengths)),
            "would_fail_original_counts": [len(bm.verts), len(bm.edges), len(bm.faces)] != expected["upstream_expected_counts"],
            "would_fail_original_area": _would_fail_almost_equal(total_area, expected["upstream_expected_area"], 4),
            "would_fail_original_length": _would_fail_almost_equal(total_length, expected["upstream_expected_length"], 4),
        })
    except Exception:
        result.update({"diagnostic_status": "error", "error": _error()})
    finally:
        if bm is not None:
            bm.free()
    return result


def run_diagnostics():
    import bpy

    result = {
        "schema": 1,
        "diagnostic_only": True,
        "acceptance_tests_modified": False,
        "upstream_commit": UPSTREAM_COMMIT,
        "expected_counts": {"vector_cases": 145, "screw_cases": 2},
        "identity": {
            "version": list(bpy.app.version),
            "version_string": bpy.app.version_string,
            "build_hash": _text(bpy.app.build_hash),
            "build_branch": _text(bpy.app.build_branch),
            "build_type": _text(bpy.app.build_type),
            "platform": sys.platform,
            "pointer_bits": struct.calcsize("P") * 8,
            "python_version": sys.version,
            "byteorder": sys.byteorder,
        },
        "errors": [],
    }
    result["vector_cases"] = [_observe_vector(i, v) for i, v in enumerate(_VECTOR_DATA)]
    result["screw_cases"] = [_observe_screw(value) for value in (False, True)]
    result["input_manifest_sha256"] = _digest({
        section: [{"id": case["id"], "inputs": case["inputs"]} for case in result[section]]
        for section in ("vector_cases", "screw_cases")
    })
    result["vector_summary"] = {
        "observed_cases": len(result["vector_cases"]),
        "zero_cases": [case["inputs"]["upstream_index"] for case in result["vector_cases"] if case["diagnostic_status"] == "skipped_zero"],
        "would_fail_original_indices": [case["inputs"]["upstream_index"] for case in result["vector_cases"] if case.get("would_fail_original_assertion")],
    }
    for section in ("vector_cases", "screw_cases"):
        for case in result[section]:
            if "error" in case:
                result["errors"].append({"section": section, "id": case["id"], "error": case["error"]})
    if all(case["diagnostic_status"] == "complete" for case in result["screw_cases"]):
        result["screw_summary"] = {
            "unique_coordinate_sets_equal_between_branches": [
                co["values"] for co in result["screw_cases"][0]["unique_coordinates_sorted"]
            ] == [co["values"] for co in result["screw_cases"][1]["unique_coordinates_sorted"]],
            "both_branches_observed": True,
        }
    return result


if __name__ == "__main__":
    print(MARKER + json.dumps(run_diagnostics(), sort_keys=True, separators=(",", ":"), allow_nan=False))
