#!/usr/bin/env python3
"""Regenerate the optional codec patch from verified pinned port source bytes."""
from __future__ import annotations
import difflib
import hashlib
import json
from pathlib import Path

EVIDENCE = Path(__file__).resolve().parent
REPO = EVIDENCE.parents[2]
PACKAGE = REPO / "patches/browser-codecs"
SOURCE = EVIDENCE / "sources/port"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def replace_once(text: str, old: str, new: str) -> str:
    if text.count(old) != 1:
        raise ValueError("expected one exact pinned source fragment: " + repr(old[:100]))
    return text.replace(old, new)


def main() -> None:
    source_index = json.loads((EVIDENCE / "source-inputs.json").read_text())
    source_rows = {row["upstream_path"]: row for row in source_index["sources"]
                   if row["repository"] == "gessa-ai/blender-web"}
    originals, outputs = {}, {}

    def original(name: str) -> str:
        data = (SOURCE / name).read_bytes()
        assert digest(data) == source_rows[name]["sha256"]
        assert len(data) == source_rows[name]["bytes"]
        originals[name] = data
        return data.decode()

    name = "patches/blender_web.cmake"
    text = original(name)
    text = replace_once(text, "# ---- Image codecs (unported / out of launch tier)",
                        "# ---- Image codecs (original pinned static implementations)")
    for flag in ("WITH_IMAGE_CINEON", "WITH_IMAGE_OPENJPEG", "WITH_IMAGE_WEBP"):
        lines = [line for line in text.splitlines() if line.startswith("set(" + flag + " ")]
        assert len(lines) == 1 and "OFF CACHE BOOL" in lines[0]
        text = replace_once(text, lines[0], lines[0].replace("OFF CACHE BOOL", "ON  CACHE BOOL"))
    outputs[name] = text.encode()

    name = "patches/platform_wasm.cmake"
    text = original(name)
    needle = "  find_package(OpenColorIO 2.0.0 REQUIRED)"
    text = replace_once(text, needle,
                        "  include(\"${BLENDER_WEB_PATCH_DIR}/image_codecs.cmake\")\n" + needle)
    outputs[name] = text.encode()

    name = "scripts/deps/openimageio.sh"
    text = original(name)
    text = replace_once(text, "# Build a TRIMMED OpenImageIO for wasm, static, -pthread.",
                        "# Build OpenImageIO with the original pinned image codecs for wasm, static, -pthread.")
    text = replace_once(text,
                        "# headless core needs (EXR, TIFF, PNG, JPEG) and disable everything else that",
                        "# headless core needs plus WebP, JPEG2000, HEIF/AVIF and DPX; disable features that")
    text = replace_once(text, "#   - no WebP/OpenJPEG/HEIF/Raw/JXL/GIF/DICOM/Ptex/FFmpeg/OpenVDB/Nuke/OpenCV/Qt/",
                        "#   - no Raw/JXL/GIF/DICOM/Ptex/FFmpeg/OpenVDB/Nuke/OpenCV/Qt/")
    text = replace_once(text, "# Idempotent: no-op once the OpenImageIO CMake config is present.",
                        "# Rebuild unconditionally: the old trimmed OIIO config cannot qualify this profile.")
    text = replace_once(text, 'NPROC="$(getconf _NPROCESSORS_ONLN)"',
                        'NPROC="${BLENDED_BUILD_JOBS:-1}"\n'
                        'case "$NPROC" in 1|2|3|4) ;; *) echo "codec builds require 1 to 4 jobs" >&2; exit 2 ;; esac\n'
                        'export EMCC_CORES="$NPROC"\n'
                        'source "$ROOT/scripts/deps/codec-common.sh"')
    start = text.index('if [ -f "$CONFIG_MARKER" ] && [ "${BW_REBUILD_OPENIMAGEIO:-0}" != 1 ]; then\n')
    end = text.index('\nfi\n', start) + len('\nfi\n')
    text = text[:start] + text[end:]
    needle = '# shellcheck disable=SC1091\nsource "$ROOT/tools/emsdk/emsdk_env.sh"'
    text = replace_once(text, needle,
                        '# Codec prerequisites were built explicitly by the selected build driver.\n'
                        'for BC_LIB in webp webpmux webpdemux sharpyuv openjp2 aom heif; do\n'
                        '  test -s "$PREFIX/lib/lib${BC_LIB}.a" || { echo "missing codec: $BC_LIB" >&2; exit 1; }\n'
                        'done\n'
                        ': "${EM_CACHE:?Set EM_CACHE to a build-specific directory}"\n'
                        'BC_EM_CACHE="$EM_CACHE"\n' + needle + '\n'
                        'export EM_CACHE="$BC_EM_CACHE"')
    text = replace_once(text, 'SRC="$SCRATCH/OpenImageIO-${OIIO_VERSION}"',
                        'bc_check_sha256 "$TARBALL" 0fc59b8e2708ded02d3793b8f3331f037ed49bfcde38158f05ac0e876ebb85b7\n\n'
                        'SRC="$SCRATCH/OpenImageIO-${OIIO_VERSION}"')
    text = replace_once(text, '-DOpenImageIO_REQUIRED_DEPS="TIFF;OpenEXR;PNG;libjpeg-turbo;fmt;Robinmap;ZLIB;OpenColorIO"',
                        '-DOpenImageIO_REQUIRED_DEPS="TIFF;OpenEXR;PNG;libjpeg-turbo;fmt;Robinmap;ZLIB;OpenColorIO;WebP;OpenJPEG;Libheif"')
    for flag in ("WEBP", "OPENJPEG", "LIBHEIF"):
        text = replace_once(text, "-DUSE_" + flag + "=OFF", "-DUSE_" + flag + "=ON")
    text = replace_once(text, '  -DOpenEXR_ROOT="$PREFIX" \\\n',
                        '  -DWebP_DIR="$PREFIX/share/WebP/cmake" \\\n'
                        '  -DOpenJPEG_DIR="$PREFIX/lib/cmake/openjpeg-2.5" \\\n'
                        '  -DLibheif_DIR="$PREFIX/lib/cmake/libheif" \\\n'
                        '  -DOpenEXR_ROOT="$PREFIX" \\\n')
    text = replace_once(text, '#include <OpenImageIO/typedesc.h>\n',
                        '#include <OpenImageIO/typedesc.h>\n#include <libheif/heif.h>\n')
    text = replace_once(text, 'int main() {\n',
                        'int main() {\n'
                        '  for (const char *format : {"webp", "jpeg2000", "heif", "dpx"}) {\n'
                        '    if (!OIIO::ImageInput::create(format) || !OIIO::ImageOutput::create(format)) {\n'
                        '      std::fprintf(stderr, "Missing required static OIIO plugin: %s\\n", format);\n'
                        '      return 2;\n'
                        '    }\n'
                        '  }\n'
                        '  if (!heif_have_encoder_for_format(heif_compression_AV1) ||\n'
                        '      !heif_have_decoder_for_format(heif_compression_AV1)) {\n'
                        '    std::fprintf(stderr, "Missing required static AV1 encoder or decoder\\n");\n'
                        '    return 3;\n'
                        '  }\n')
    text = replace_once(text, '  "$PREFIX"/lib/libOpenColorIO.a \\\n',
                        '  "$PREFIX"/lib/libOpenColorIO.a \\\n'
                        '  "$PREFIX"/lib/libwebp.a \\\n'
                        '  "$PREFIX"/lib/libwebpmux.a \\\n'
                        '  "$PREFIX"/lib/libwebpdemux.a \\\n'
                        '  "$PREFIX"/lib/libsharpyuv.a \\\n'
                        '  "$PREFIX"/lib/libopenjp2.a \\\n'
                        '  "$PREFIX"/lib/libheif.a \\\n'
                        '  "$PREFIX"/lib/libaom.a \\\n')
    text = replace_once(text, 'echo "openimageio: verify link+physical-memory runtime OK"',
                        'echo "openimageio: verify static codecs, AV1 backends, link and physical-memory runtime OK"')
    text = replace_once(text, 'rm -rf "$SCRATCH"\necho "openimageio ',
                        '# Preserve exact generated configuration for the outer build receipt.\n'
                        'python3 - "$BUILD/CMakeCache.txt" <<\'PY\'\n'
                        'from pathlib import Path\n'
                        'import re, sys\n'
                        'values = {}\n'
                        'for line in Path(sys.argv[1]).read_text().splitlines():\n'
                        '    match = re.fullmatch(r"([^:#][^:]*):[^=]+=(.*)", line)\n'
                        '    if match: values[match[1]] = match[2]\n'
                        'expected = {"USE_WEBP": "ON", "USE_OPENJPEG": "ON", "USE_LIBHEIF": "ON", "EMBEDPLUGINS": "ON", "BUILD_SHARED_LIBS": "OFF"}\n'
                        'for key, value in expected.items():\n'
                        '    if values.get(key) != value:\n'
                        '        raise SystemExit(f"Required OIIO configuration missing: {key}={value}")\n'
                        'PY\n'
                        'mkdir -p "$PREFIX/share/blended"\n'
                        'install -m644 "$BUILD/CMakeCache.txt" "$PREFIX/share/blended/openimageio-codecs-CMakeCache.txt"\n\n'
                        'rm -rf "$SCRATCH"\necho "openimageio ')
    outputs[name] = text.encode()

    for path in sorted((PACKAGE / "recipes").glob("*.sh")):
        outputs["scripts/deps/" + path.name] = path.read_bytes()
    for path in sorted((PACKAGE / "dependency-patches").glob("*.patch")):
        outputs["scripts/deps/" + path.name] = path.read_bytes()
    outputs["patches/image_codecs.cmake"] = (PACKAGE / "image_codecs.cmake").read_bytes()

    entries, chunks = [], []
    for name, data in sorted(outputs.items()):
        old = originals.get(name)
        entries.append({"path": name, "before_sha256": digest(old) if old is not None else None,
                        "after_sha256": digest(data), "after_bytes": len(data)})
        chunks.append("diff --git a/" + name + " b/" + name + "\n")
        if old is None:
            chunks.append("new file mode 100644\n")
        chunks.append("".join(difflib.unified_diff((old or b"").decode().splitlines(True), data.decode().splitlines(True),
                                                  fromfile="a/" + name if old is not None else "/dev/null", tofile="b/" + name)))
    patch_path = PACKAGE / "0001-enable-original-image-codecs.patch"
    patch_bytes = "".join(chunks).encode()
    patch_path.write_bytes(patch_bytes)
    dependencies = json.loads((EVIDENCE / "dependency-inputs.json").read_text())["archives"]
    manifest = {
        "schema": 1, "id": "blender-5.2.0-web-codecs-v1",
        "port": {"repository": "https://github.com/gessa-ai/blender-web", "commit": "0e02e84b2bc5d9b27a6dc6e275443292f781fbad"},
        "upstream_blender": {"repository": "https://github.com/blender/blender", "commit": "fbe6228777e7d9afefcd61a413844e790ae75db7"},
        "emsdk": {"version": "6.0.5", "compiler_commit": "1db513782be24469589d7cb8a1f1834e9a33f271"},
        "patch": {"file": patch_path.name, "bytes": len(patch_bytes), "sha256": digest(patch_bytes)},
        "application_helper": {"file": "apply.py", "bytes": (PACKAGE / "apply.py").stat().st_size,
                               "sha256": digest((PACKAGE / "apply.py").read_bytes())},
        "files": entries,
        "dependencies": [{key: row[key] for key in ("name", "version", "url", "bytes", "sha256", "upstream_archive_hash")}
                         for row in dependencies],
        "dependency_recipe_insertion": {"before": "openimageio", "recipes": ["webp", "openjpeg", "aom", "libheif"]},
        "required_blender_cache": {key: "ON" for key in ("WITH_IMAGE_CINEON", "WITH_IMAGE_OPENJPEG", "WITH_IMAGE_WEBP")},
        "required_oiio_cache": {"USE_WEBP": "ON", "USE_OPENJPEG": "ON", "USE_LIBHEIF": "ON", "EMBEDPLUGINS": "ON", "BUILD_SHARED_LIBS": "OFF"},
        "required_environment": ["EM_CACHE"],
        "installed_oiio_configuration": "lib/wasm/share/blended/openimageio-codecs-CMakeCache.txt",
        "cache_policy": "Rebuild four codec dependencies and OIIO from verified archives. An installed config marker does not skip any of these five recipes. Bind this manifest in the outer dependency-cache key.",
        "scope": "Original Blender ImBuf codec implementations and their pinned dependencies; no upstream assertions, test selectors, tolerances or expected outcomes change.",
        "blender_cases_executed": 0, "full_feature_parity": False,
        "limits": ["Dependency compilation and recipe smoke probes do not establish original Blender test parity.",
                   "CINEON and DPX compile and original 80-parent, 57-subtest ImBuf conformance require a new complete Blender browser build.",
                   "The Libheif source guard disables only unused standalone Embind wrappers for static C API embedding."]}
    path = PACKAGE / "manifest.json"
    path.write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({"manifest": str(path.relative_to(REPO)), "bytes": path.stat().st_size, "sha256": digest(path.read_bytes()),
                      "patch_sha256": digest(patch_bytes), "changed_files": len(entries)}))


if __name__ == "__main__":
    main()
