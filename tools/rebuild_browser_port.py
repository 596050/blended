#!/usr/bin/env python3
"""Reconstruct and build one pinned Blender browser DEVELOPMENT artifact.

This is an OFF-mode source qualification build, not a reproduction of the
published v0.1.1 binary or the upstream hardware-gated shipping split profile.
The pinned port's feature configuration and dependency recipes are retained.
Only build metadata, bounded parallelism and build-tool pinning are adjusted.
Every command writes a receipt before execution, including failures/timeouts.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shutil
import signal
import subprocess
import sys
import tarfile
import time
import traceback

PORT_COMMIT = "0e02e84b2bc5d9b27a6dc6e275443292f781fbad"
UPSTREAM_COMMIT = "fbe6228777e7d9afefcd61a413844e790ae75db7"
PATCH_SHA256 = "04ba2e6ba8a04ef37bdaf879b10a135736f07114597a908bbbdea8bba244193c"
PATCH_BYTES = 2447156
EMSDK_COMMIT = "1ab2e627b1a84567f5284d1baaa5f6be7ccf07de"
EMSCRIPTEN_VERSION = "6.0.5"
EMSCRIPTEN_RELEASE = "dbd755b5da399329c2576f6e3dfa7f419f5d8409"
EMSCRIPTEN_COMPILER = "1db513782be24469589d7cb8a1f1834e9a33f271"
DAWN_COMMIT = "36cf1fae0cd8a81a4fb4580751648b80b2e6255c"
BLENDER_LFS_URL = "https://projects.blender.org/blender/blender.git/info/lfs"
DEPENDENCIES = (
    "zlib zstd fmt eigen robinmap imath libdeflate openjph openexr libjpeg "
    "libpng libtiff expat yamlcpp pystring minizipng opencolorio brotli "
    "freetype tbb openimageio tint shaderc python wheels numpy opensubdiv openusd"
).split()

# These exact entries are present in Dawn's DEPS at DAWN_COMMIT. The existing
# Tint/shaderc recipes disable the other platform backends. No engine feature
# is disabled by selecting this build dependency closure.
DAWN_DEPS = {
    "third_party/abseil-cpp": ("https://chromium.googlesource.com/chromium/src/third_party/abseil-cpp", "63f52bfdb2ebc0ef3add13b98af45778d0040278"),
    "third_party/jinja2": ("https://chromium.googlesource.com/chromium/src/third_party/jinja2", "c3027d884967773057bf74b957e3fea87e5df4d7"),
    "third_party/markupsafe": ("https://chromium.googlesource.com/chromium/src/third_party/markupsafe", "4256084ae14175d38a3ff7d739dca83ae49ccec6"),
    "third_party/spirv-headers/src": ("https://chromium.googlesource.com/external/github.com/KhronosGroup/SPIRV-Headers", "4015a331f5ffd6fc5c6fa7b03e08fb4a692491d7"),
    "third_party/spirv-tools/src": ("https://chromium.googlesource.com/external/github.com/KhronosGroup/SPIRV-Tools", "a9cdf5bdd25d516294b5c25502b67e6116ed7eb5"),
    "third_party/glslang/src": ("https://chromium.googlesource.com/external/github.com/KhronosGroup/glslang", "8d6dd0e41424c25806ca20523430f2e4c3aeb1a1"),
    "third_party/webgpu-headers/src": ("https://chromium.googlesource.com/external/github.com/webgpu-native/webgpu-headers", "01addc4ba8a2915a061b7095a6768b512071ab96"),
    "third_party/googletest": ("https://chromium.googlesource.com/external/github.com/google/googletest", "4fe3307fb2d9f86d19777c7eb0e4809e9694dde7"),
}

# Verified public PyPI wheel hashes. All transitive host Python dependencies are
# included, and pip is invoked with --no-deps --require-hashes. These are build
# tools, not substitutions for Blender's embedded Python/NumPy versions.
HOST_REQUIREMENTS = """cmake==4.0.3 --hash=sha256:d840e780c48c5df1330879d50615176896e8e6eee554507d21ce8e2f1a5f0ff8
ninja==1.13.0 --hash=sha256:fb46acf6b93b8dd0322adc3a4945452a4e774b75b91293bafcc7b7f8e6517dfa
meson==1.9.1 --hash=sha256:f824ab770c041a202f532f69e114c971918ed2daff7ea56583d80642564598d0
meson-python==0.18.0 --hash=sha256:3b0fe051551cc238f5febb873247c0949cd60ded556efa130aa57021804868e2
Cython==3.1.4 --hash=sha256:c3f3bb603f28b3c1df66baaa5cdbf6029578552b458f1d321bae23b87f6c3199 --hash=sha256:d194d95e4fa029a3f6c7d46bdd16d973808c7ea4797586911fdb67cb98b1a2c6
packaging==25.0 --hash=sha256:29572ef2b1f17581046b3a2227d5c611fb25ec70ca1ba8554b24b0e69331a484
pyproject-metadata==0.9.1 --hash=sha256:ee5efde548c3ed9b75a354fc319d5afd25e9585fa918a34f62f904cc731973ad
pip==25.2 --hash=sha256:6d67a2b4e7f14d8b31b8b52648866fa717f45a1eb70e83002f4331d07e953717
"""


class Blocked(RuntimeError):
    pass


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def digest(path: Path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return {"path": str(path), "bytes": path.stat().st_size, "sha256": h.hexdigest()}


def write_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(data, indent=2) + "\n")
    temp.replace(path)


class Build:
    def __init__(self, args):
        self.args = args
        self.work = args.work_dir.resolve()
        self.out = args.output.resolve()
        self.port = self.work / "gessa"
        self.upstream = self.port / "upstream"
        self.sdk = self.port / "tools/emsdk"
        self.build_dir = self.port / "build-wasm-development-off"
        self.out.mkdir(parents=True, exist_ok=True)
        (self.out / "logs").mkdir(exist_ok=True)
        self.work.mkdir(parents=True, exist_ok=True)
        self.env = dict(os.environ)
        # Host Python contamination broke an existing port's NumPy build.
        for key in ("PYTHONPATH", "PYTHONHOME", "_PYTHON_SYSCONFIGDATA_NAME", "CC", "CXX", "AR", "RANLIB"):
            self.env.pop(key, None)
        self.env.update({
            "GIT_LFS_SKIP_SMUDGE": "1", "GIT_TERMINAL_PROMPT": "0",
            "EMSDK_KEEP_DOWNLOADS": "1", "EMSDK_PYTHON": sys.executable,
            "CMAKE_BUILD_PARALLEL_LEVEL": str(args.jobs), "MAKEFLAGS": f"-j{args.jobs}",
            "CCACHE_DIR": str(self.work / "ccache"), "CCACHE_MAXSIZE": "2G",
            "EM_CACHE": str(self.work / "emscripten-cache"), "EM_COMPILER_WRAPPER": "ccache",
            "BLENDED_BUILD_JOBS": str(args.jobs), "BLENDED_SOURCE_EVIDENCE": str(self.out),
        })
        self.data = {
            "schema": 1, "artifact_kind": "blender-source-development", "status": "running",
            "started_utc": now(), "port_commit": PORT_COMMIT, "upstream_commit": UPSTREAM_COMMIT,
            "canonical_patch_sha256": PATCH_SHA256, "build_mode": "OFF", "with_buildinfo": False,
            "deployed": False, "shipping_profile": False, "hardware_verified": False,
            "full_feature_parity": False, "tests_executed": False,
            "reproduces_published_release": False, "bitwise_reproducibility_verified": False,
            "build_tool_differences": ["Ninja 1.13.0 from a verified PyPI wheel; the port runbook names 1.13.1."],
            "jobs": args.jobs, "entry_point": digest(Path(__file__).resolve()),
            "source_checkouts": [], "stages": [], "dependency_receipts": [], "recipe_overlays": [],
            "limits": [
                "A new OFF-mode artifact at the inspected port HEAD; not the v0.1.1 release source.",
                "Source commits and recipe bytes are pinned; some upstream archives declare MD5. New SHA256 observations are receipts, not independently prevalidated locks.",
                "Ubuntu package revisions are inventoried, not a hermetic pinned operating-system image.",
                "Shipping CAPTURE/APPLY requires hardware profiles and is not attempted.",
            ],
        }
        self.process = None
        self.save()

    def save(self):
        write_json(self.out / "source-build.json", self.data)

    def run(self, name, argv, cwd=None, env=None, timeout=None):
        cwd = Path(cwd or self.port)
        log = self.out / "logs" / f"{len(self.data['stages']):03d}-{name}.log"
        stage = {"name": name, "argv": [str(x) for x in argv], "cwd": str(cwd),
                 "started_utc": now(), "status": "running", "log": str(log)}
        self.data["stages"].append(stage)
        self.save()
        print(f"SOURCE BUILD: {name}", flush=True)
        start = time.monotonic()
        limit = timeout or self.args.stage_timeout
        try:
            with log.open("wb") as stream:
                self.process = subprocess.Popen(stage["argv"], cwd=cwd, env=env or self.env,
                                                stdout=stream, stderr=subprocess.STDOUT, start_new_session=True)
                while True:
                    try:
                        rc = self.process.wait(timeout=30)
                        break
                    except subprocess.TimeoutExpired:
                        elapsed = time.monotonic() - start
                        stage["elapsed_seconds"] = round(elapsed, 3)
                        self.save()
                        print(f"SOURCE BUILD: {name}, {int(elapsed)} seconds, log {log.stat().st_size} bytes", flush=True)
                        if elapsed >= limit:
                            os.killpg(self.process.pid, signal.SIGTERM)
                            try:
                                self.process.wait(timeout=10)
                            except subprocess.TimeoutExpired:
                                os.killpg(self.process.pid, signal.SIGKILL)
                                self.process.wait()
                            raise Blocked(f"stage {name} exceeded {limit} seconds")
            stage["exit_code"] = rc
            stage["status"] = "passed" if rc == 0 else "failed"
            if rc:
                tail = log.read_bytes()[-12000:].decode("utf-8", "replace")
                print(tail, flush=True)
                raise RuntimeError(f"stage {name} failed with exit code {rc}; see {log.name}")
            return log.read_text(errors="replace")
        except BaseException:
            if stage["status"] == "running":
                stage["status"] = "blocked"
            raise
        finally:
            self.process = None
            stage["finished_utc"] = now()
            stage["duration_seconds"] = round(time.monotonic() - start, 3)
            # Bound artifact storage while retaining the beginning and final error.
            if log.exists() and log.stat().st_size > 16 * 1024 * 1024:
                size = log.stat().st_size
                with log.open("rb") as f:
                    head = f.read(1024 * 1024)
                    f.seek(-14 * 1024 * 1024, 2)
                    tail = f.read()
                log.write_bytes(head + b"\n[LOG MIDDLE TRUNCATED BY RECEIPT LIMIT]\n" + tail)
                stage["log_original_bytes"] = size
                stage["log_truncated"] = True
            if log.exists():
                stage["log_identity"] = digest(log)
            self.save()

    def git(self, name, path, url, commit):
        path.mkdir(parents=True, exist_ok=True)
        if not (path / ".git").exists():
            self.run(name + "-init", ["git", "init", "--initial-branch=source-input"], path)
            self.run(name + "-remote", ["git", "remote", "add", "origin", url], path)
        # A filtered fetch into a newly initialized repository must persist its
        # promisor remote so checkout can retrieve the missing immutable blobs.
        self.run(name + "-promisor", ["git", "config", "remote.origin.promisor", "true"], path)
        self.run(name + "-filter", ["git", "config", "remote.origin.partialclonefilter", "blob:none"], path)
        # Never execute repository hooks from cached checkouts.
        command = ["git", "-c", "core.hooksPath=/dev/null"]
        self.run(name + "-fetch", command + ["fetch", "--depth=1", "--filter=blob:none", "origin", commit], path, timeout=900)
        self.run(name + "-checkout", command + ["checkout", "--detach", commit], path, timeout=900)
        actual = self.run(name + "-identity", ["git", "rev-parse", "HEAD"], path).strip()
        if actual != commit:
            raise Blocked(f"{name} commit mismatch: {actual}")
        self.data["source_checkouts"].append({"name": name, "url": url, "commit": actual, "path": str(path)})
        self.save()

    def reconstruct(self):
        self.git("port", self.port, "https://github.com/gessa-ai/blender-web.git", PORT_COMMIT)
        patch = self.port / "patches/PREVIEW_SNAPSHOT.patch"
        patch_id = digest(patch)
        receipt = json.loads((self.port / "sandbox/series-replay/canonical-freeze-receipt.json").read_text())
        canonical = [s.strip() for s in (self.port / "patches/canonical").read_text().splitlines() if s.strip() and not s.lstrip().startswith("#")]
        if (patch_id["sha256"] != PATCH_SHA256 or patch_id["bytes"] != PATCH_BYTES
                or receipt["patch"]["sha256"] != PATCH_SHA256 or receipt["expected_pin"] != UPSTREAM_COMMIT
                or canonical != [patch.name]):
            raise Blocked("canonical source patch identity mismatch")
        self.data["canonical_patch"] = patch_id
        self.git("blender", self.upstream, "https://github.com/blender/blender.git", UPSTREAM_COMMIT)
        marker = self.work / "source-reconstructed.json"
        status = self.run("source-status", ["git", "status", "--porcelain=v1", "--untracked-files=all"], self.upstream)
        if status:
            if not marker.exists() or json.loads(marker.read_text()).get("patch") != PATCH_SHA256:
                raise Blocked("existing source worktree differs without a matching reconstruction receipt")
            self.run("canonical-already-applied", ["git", "apply", "--reverse", "--check", str(patch)], self.upstream)
        else:
            self.run("canonical-check", ["git", "apply", "--check", str(patch)], self.upstream)
            self.run("canonical-apply", ["git", "apply", str(patch)], self.upstream)
            write_json(marker, {"upstream": UPSTREAM_COMMIT, "port": PORT_COMMIT, "patch": PATCH_SHA256})
        self.run("source-diff", ["git", "diff", "--stat"], self.upstream)
        epoch = self.run("source-epoch", ["git", "show", "-s", "--format=%ct", UPSTREAM_COMMIT], self.upstream).strip()
        if not epoch.isdigit():
            raise Blocked("invalid source commit timestamp")
        self.env["SOURCE_DATE_EPOCH"] = epoch
        self.data["source_date_epoch"] = int(epoch)
        self.data["source_reconstructed"] = True
        self.data["declared_feature_configuration"] = digest(self.port / "patches/blender_web.cmake")
        self.data["declared_disabled_features"] = sorted(set(re.findall(
            r"set\((WITH_\w+)\s+OFF\s+CACHE", (self.port / "patches/blender_web.cmake").read_text())))
        self.save()

    def install_shims(self):
        shims = self.work / "build-shims"
        shims.mkdir(exist_ok=True)
        real_curl = shutil.which("curl", path=self.env["PATH"])
        real_getconf = shutil.which("getconf", path=self.env["PATH"])
        real_ninja = shutil.which("ninja", path=self.env["PATH"])
        if not all((real_curl, real_getconf, real_ninja)):
            raise Blocked("curl, getconf and pinned Ninja are required")
        # Preserve exact recipe argv; only observe successful curl downloads.
        curl_code = f'''#!{sys.executable}
import hashlib,json,os,subprocess,sys,time
from pathlib import Path
a=sys.argv[1:];r=subprocess.run([{real_curl!r},*a]);out=None
for i,x in enumerate(a):
 if x in ('-o','--output') and i+1<len(a): out=a[i+1]
 if x.startswith('--output='): out=x.split('=',1)[1]
if r.returncode==0 and out and Path(out).is_file():
 p=Path(out);h=hashlib.sha256()
 with p.open('rb') as f:
  for chunk in iter(lambda:f.read(1048576),b''):h.update(chunk)
 row={{'observed_utc_epoch':time.time(),'url':[x for x in a if x.startswith(('https://','http://'))],'path':str(p.resolve()),'bytes':p.stat().st_size,'sha256':h.hexdigest(),'digest_role':'observed_after_download'}}
 with open(Path(os.environ['BLENDED_SOURCE_EVIDENCE'])/'downloads.jsonl','a') as f:f.write(json.dumps(row)+'\\n')
sys.exit(r.returncode)
'''
        (shims / "curl").write_text(curl_code)
        (shims / "getconf").write_text(f'''#!{sys.executable}
import os,subprocess,sys
if sys.argv[1:]==['_NPROCESSORS_ONLN']: print(os.environ['BLENDED_BUILD_JOBS'])
else: sys.exit(subprocess.call([{real_getconf!r},*sys.argv[1:]]))
''')
        (shims / "ninja").write_text(f'''#!{sys.executable}
import os,subprocess,sys
args=[];skip=False
for a in sys.argv[1:]:
 if skip:skip=False;continue
 if a=='-j':skip=True;continue
 if a.startswith('-j') and a[2:].isdigit():continue
 args.append(a)
sys.exit(subprocess.call([{real_ninja!r},'-j'+os.environ['BLENDED_BUILD_JOBS'],*args]))
''')
        for p in shims.iterdir():
            p.chmod(0o755)
        self.env["PATH"] = str(shims) + os.pathsep + self.env["PATH"]

    def toolchain(self):
        if platform.system() != "Linux" or platform.machine() not in ("x86_64", "AMD64"):
            raise Blocked("this source-build profile targets Linux x86_64 hosts")
        if sys.version_info[:2] != (3, 13):
            raise Blocked("run with native Python 3.13; NumPy's cross build requires the target minor")
        requirements = self.work / "host-requirements.txt"
        requirements.write_text(HOST_REQUIREMENTS)
        self.env["BLENDED_HOST_REQUIREMENTS"] = str(requirements)
        self.data["host_requirements"] = digest(requirements)
        self.run("host-python-tools", [sys.executable, "-m", "pip", "install", "--disable-pip-version-check",
                 "--only-binary=:all:", "--require-hashes", "--no-deps", "-r", str(requirements)], self.work, timeout=600)
        self.install_shims()
        self.run("host-packages", ["dpkg-query", "-W", "-f=${Package}\t${Version}\n"], self.work)
        self.run("host-python-freeze", [sys.executable, "-m", "pip", "freeze", "--all"], self.work)
        self.run("host-platform", ["uname", "-a"], self.work)
        self.run("host-storage", ["df", "-h", str(self.work)], self.work)
        self.git("emsdk", self.sdk, "https://github.com/emscripten-core/emsdk.git", EMSDK_COMMIT)
        tags = json.loads((self.sdk / "emscripten-releases-tags.json").read_text())
        if tags["releases"][EMSCRIPTEN_VERSION] != EMSCRIPTEN_RELEASE:
            raise Blocked("Emscripten release manifest mismatch")
        self.run("emsdk-install", [sys.executable, str(self.sdk / "emsdk.py"), "install", EMSCRIPTEN_VERSION], self.sdk, timeout=1800)
        self.run("emsdk-activate", [sys.executable, str(self.sdk / "emsdk.py"), "activate", EMSCRIPTEN_VERSION], self.sdk)
        em = self.sdk / "upstream/emscripten"
        node = self.sdk / "node/22.16.0_64bit/bin/node"
        self.env["PATH"] = os.pathsep.join((str(self.work / "build-shims"), str(em), str(node.parent), self.env["PATH"]))
        self.env.update({"EMSDK": str(self.sdk), "EMSDK_NODE": str(node), "EM_CONFIG": str(self.sdk / ".emscripten")})
        compiler = self.run("compiler-identity", [str(em / "emcc"), "--version"], self.port)
        node_version = self.run("node-identity", [str(node), "--version"], self.port).strip()
        if EMSCRIPTEN_COMPILER not in compiler or EMSCRIPTEN_VERSION not in compiler or node_version != "v22.16.0":
            raise Blocked("compiler or Node identity mismatch")
        self.data["compiler"] = {"emsdk_commit": EMSDK_COMMIT, "release": EMSCRIPTEN_RELEASE,
                                 "version": EMSCRIPTEN_VERSION, "commit": EMSCRIPTEN_COMPILER,
                                 "node_version": node_version, "emcc": digest(em / "emcc"),
                                 "clang": digest(self.sdk / "upstream/bin/clang")}
        for command in (["cmake", "--version"], ["ninja", "--version"], ["clang++-17", "--version"], [sys.executable, "-VV"]):
            self.run("host-tool-" + Path(command[0]).name, command, self.work)
        archives = [digest(p) for p in self.sdk.rglob("*") if p.is_file() and (p.name.endswith((".tar.xz", ".tar.gz", ".zip"))) and "node_modules" not in p.parts]
        write_json(self.out / "toolchain-downloads.json", {"digest_role": "observed_after_sdk_install", "archives": archives})
        self.data["toolchain_download_receipt"] = digest(self.out / "toolchain-downloads.json")
        self.save()

    def dawn(self):
        path = self.port / "build-dawn/dawn"
        self.git("dawn", path, "https://github.com/google/dawn.git", DAWN_COMMIT)
        deps = (path / "DEPS").read_text()
        for rel, (url, pin) in DAWN_DEPS.items():
            match = re.search(r"'" + re.escape(rel) + r"':\s*\{\s*'url':\s*'([^']+)'", deps)
            if not match or not match[1].endswith("@" + pin):
                raise Blocked(f"Dawn dependency pin absent from exact DEPS: {rel}")
            self.git("dawn-" + rel.replace("/", "-"), path / rel, url, pin)
        self.data["dawn_deps_manifest"] = digest(path / "DEPS")

    def dependencies(self):
        self.dawn()
        # Blender's GitHub mirror carries pointers, not the LFS objects. The
        # exact upstream make_update.py:lfs_fallback_setup uses this official
        # projects.blender.org repository for that case. Keep the source remote
        # pinned to GitHub and select the canonical LFS endpoint for this read.
        preload = json.loads(self.run("blender-preload-lfs-index", ["git", "lfs", "ls-files", "--json",
            "--include=release/datafiles/*"], self.upstream))["files"]
        if not preload:
            raise Blocked("the pinned source has no preload LFS pointers")
        self.run("blender-preload-lfs", ["git", "-c", "lfs.url=" + BLENDER_LFS_URL, "lfs", "pull",
            "--include=release/datafiles/*"], self.upstream, timeout=900)
        preload_receipt = {"endpoint": BLENDER_LFS_URL, "status": "running",
            "expected_identity_source": "LFS pointer OIDs in the exact upstream Git index",
            "source_commit": UPSTREAM_COMMIT, "files": []}
        preload_manifest = self.out / "blender-preload-lfs.json"
        try:
            for pointer in preload:
                relative = Path(pointer["name"])
                if (relative.is_absolute() or ".." in relative.parts
                        or not relative.as_posix().startswith("release/datafiles/")
                        or pointer["oid_type"] != "sha256"):
                    raise Blocked("unexpected preload LFS pointer metadata")
                path = self.upstream / relative
                if not path.is_file() or path.is_symlink():
                    raise Blocked(f"preload data missing or not a regular file: {relative}")
                observed = digest(path)
                observed["path"] = relative.as_posix()
                row = {"path": relative.as_posix(), "expected_sha256": pointer["oid"],
                       "expected_bytes": pointer["size"], "observed": observed}
                row["verified"] = observed["sha256"] == pointer["oid"] and observed["bytes"] == pointer["size"]
                preload_receipt["files"].append(row)
                if not row["verified"]:
                    raise Blocked(f"preload bytes do not match the pinned LFS pointer: {relative}")
            preload_receipt["status"] = "verified"
            preload_receipt["verified_files"] = len(preload)
            preload_receipt["verified_bytes"] = sum(p["size"] for p in preload)
        finally:
            if preload_receipt["status"] == "running":
                preload_receipt["status"] = "blocked"
            write_json(preload_manifest, preload_receipt)
            self.data["preload_data_receipt"] = digest(preload_manifest)
            self.save()
        self.run("blender-lfs-check", ["git", "lfs", "fsck", "--pointers"], self.upstream, timeout=300)
        # Record and narrowly replace only NumPy's unpinned build-tool installs.
        recipe = self.port / "scripts/deps/numpy.sh"
        old = recipe.read_text()
        original = subprocess.run(["git", "show", PORT_COMMIT + ":scripts/deps/numpy.sh"], cwd=self.port,
                                  capture_output=True, text=True, check=True).stdout
        floating = ('  "$VENV/bin/python" -m pip install --quiet --upgrade pip\n'
                    '  "$VENV/bin/python" -m pip install --quiet "meson>=1.4" "meson-python>=0.16" ninja "cython>=3.0"')
        pinned = '  "$VENV/bin/python" -m pip install --quiet --require-hashes --only-binary=:all: --no-deps -r "$BLENDED_HOST_REQUIREMENTS"'
        if original.count(floating) != 1 or old not in (original, original.replace(floating, pinned)):
            raise Blocked("NumPy host-tool recipe seam changed")
        recipe.write_text(original.replace(floating, pinned))
        self.data["recipe_overlays"].append({"path": "scripts/deps/numpy.sh", "purpose": "Pin host build tools only",
            "original_sha256": hashlib.sha256(original.encode()).hexdigest(), "executed": digest(recipe),
            "host_requirements": self.data["host_requirements"]})
        source_recipes = {name: digest(self.port / "scripts/deps" / (name + ".sh")) for name in DEPENDENCIES}
        write_json(self.out / "dependency-recipe-inputs.json", source_recipes)
        self.data["dependency_recipe_manifest"] = digest(self.out / "dependency-recipe-inputs.json")
        self.save()
        for name in DEPENDENCIES:
            args = ["bash", str(self.port / "scripts/deps" / (name + ".sh"))]
            if name == "openusd":
                args.append(f"--jobs={self.args.jobs}")
            before = time.monotonic()
            self.run("dependency-" + name, args, self.port)
            self.data["dependency_receipts"].append({"name": name, "status": "recipe_completed",
                "recipe": source_recipes[name], "duration_seconds": round(time.monotonic() - before, 3)})
            self.save()
        manifest = self.out / "dependency-harvest.jsonl"
        with manifest.open("w") as stream:
            for p in sorted((self.port / "lib/wasm").rglob("*")):
                if p.is_file() and not p.is_symlink():
                    row = digest(p)
                    row["path"] = str(p.relative_to(self.port / "lib/wasm"))
                    stream.write(json.dumps(row) + "\n")
        self.data["dependency_harvest_manifest"] = digest(manifest)
        self.save()

    def configure(self):
        native_env = dict(self.env, CXX="clang++-17", CC="clang-17")
        self.run("native-code-generators", ["bash", "scripts/build-hosttools.sh"], self.port, native_env)
        self.run("locale-catalogs", ["bash", "scripts/build-locale-datafiles.sh"], self.port)
        env = dict(self.env, BLENDER_WEB_WINDOWED="1")
        command = ["cmake", "-S", str(self.upstream), "-B", str(self.build_dir), "-G", "Ninja",
            "-C", str(self.port / "patches/blender_web.cmake"),
            "-DCMAKE_TOOLCHAIN_FILE=" + str(self.sdk / "upstream/emscripten/cmake/Modules/Platform/Emscripten.cmake"),
            "-DCMAKE_BUILD_TYPE=Release", "-DWITH_BLENDER_WEB_BROWSER=ON", "-DWITH_BUILDINFO=ON",
            "-DBLENDER_WEB_WASM_SPLIT_MODE=OFF", "-DCMAKE_EXE_LINKER_FLAGS=-g0",
            "-DCMAKE_EXPORT_COMPILE_COMMANDS=ON", "-DCMAKE_C_COMPILER_LAUNCHER=ccache", "-DCMAKE_CXX_COMPILER_LAUNCHER=ccache",
            "-DPYTHON_EXECUTABLE=" + sys.executable]
        self.run("configure-engine", command, self.port, env)
        cache = self.build_dir / "CMakeCache.txt"
        values = {}
        for line in cache.read_text().splitlines():
            m = re.match(r"([^/#][^:]*):([^=]+)=(.*)", line)
            if m:
                values[m[1]] = m[3]
        if values.get("WITH_BUILDINFO") != "ON" or values.get("BLENDER_WEB_WASM_SPLIT_MODE") != "OFF":
            raise Blocked("configured build metadata/profile does not match the qualification contract")
        required = ("WITH_PYTHON", "WITH_TBB", "WITH_CYCLES", "WITH_OPENSUBDIV", "WITH_USD", "WITH_INTERNATIONAL", "WITH_WEBGPU_BACKEND", "WITH_GHOST_WEB", "WITH_GTESTS")
        if any(values.get(x) != "ON" for x in required):
            raise Blocked("the configured engine lost a required feature from the pinned port profile")
        self.data["with_buildinfo"] = True
        self.data["configured_features"] = {k: v for k, v in values.items() if k.startswith("WITH_")}
        self.data["disabled_features"] = sorted(k for k, v in self.data["configured_features"].items() if v == "OFF")
        for p in (cache, self.build_dir / "compile_commands.json"):
            if p.exists():
                shutil.copy2(p, self.out / p.name)
        self.data["configuration"] = digest(self.out / "CMakeCache.txt")
        self.data["compile_commands"] = digest(self.out / "compile_commands.json")
        self.save()

    def compile(self):
        # The port clones creator sources into blender_browser but does not
        # clone blender's explicit buildinfo target dependency. Generate the
        # upstream header first; leave the engine sources unchanged.
        self.run("generate-build-identity", ["ninja", "-C", str(self.build_dir), "buildinfo"], self.port)
        self.run("compile-engine", ["ninja", "-C", str(self.build_dir), f"-j{self.args.jobs}", "blender_browser"], self.port,
                 timeout=self.args.build_timeout)
        self.run("link-command-receipt", ["ninja", "-C", str(self.build_dir), "-t", "commands", "blender_browser"], self.port)

    def package(self):
        bundle = self.work / "development-bundle"
        if bundle.exists():
            shutil.rmtree(bundle)
        (bundle / "bin").mkdir(parents=True)
        shell = self.port / "platform_web/shell"
        if any(p.is_symlink() for p in shell.rglob("*")):
            raise Blocked("source shell contains links; inspect before packaging")
        shutil.copytree(shell, bundle / "shell")
        binaries = self.build_dir / "bin"
        for suffix in (".js", ".wasm", ".data"):
            p = binaries / ("blender_browser" + suffix)
            if not p.is_file() or p.is_symlink() or p.stat().st_size == 0:
                raise Blocked(f"expected browser output missing: {p}")
        for p in sorted(binaries.glob("blender_browser*")):
            if p.is_file() and p.suffix in (".js", ".wasm", ".data", ".mjs"):
                if p.is_symlink():
                    raise Blocked("browser output contains a symlink")
                shutil.copy2(p, bundle / "bin" / p.name)
        for name in ("LICENSE", "NOTICE", "PROVENANCE.md", "THIRD-PARTY.md"):
            p = self.port / name
            if p.is_file():
                shutil.copy2(p, bundle / name)
        shutil.copytree(self.port / "LICENSES", bundle / "LICENSES")
        artifact = self.out / "blender-source-development.tar.gz"
        # Fixed metadata makes packaging deterministic for the same file bytes.
        import gzip
        with artifact.open("wb") as raw, gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as zipped:
            with tarfile.open(fileobj=zipped, mode="w") as archive:
                for p in sorted(bundle.rglob("*")):
                    if not p.is_file() or p.is_symlink():
                        continue
                    info = archive.gettarinfo(str(p), arcname="blender-source-development/" + p.relative_to(bundle).as_posix())
                    info.uid = info.gid = 0
                    info.uname = info.gname = ""
                    info.mtime = 0
                    info.mode = 0o644
                    with p.open("rb") as stream:
                        archive.addfile(info, stream)
        self.data["artifact"] = digest(artifact)
        self.data["engine_files"] = [digest(p) for p in sorted((bundle / "bin").iterdir())]
        self.data["status"] = "built"
        self.data["reason"] = "Pinned canonical source built with the original feature profile, build metadata enabled, and OFF development packaging. Runtime tests remain required."
        self.save()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work-dir", type=Path, default=Path(".cache/browser-source"))
    parser.add_argument("--output", type=Path, default=Path("evidence/browser-source-build"))
    parser.add_argument("--jobs", type=int, default=2)
    parser.add_argument("--stage-timeout", type=int, default=5400)
    parser.add_argument("--build-timeout", type=int, default=10800)
    parser.add_argument("--stop-after", choices=("source", "toolchain", "dependencies", "configure", "build"), default="build")
    args = parser.parse_args()
    if not 1 <= args.jobs <= 4:
        parser.error("--jobs must be between 1 and 4 for this free-runner profile")
    b = Build(args)
    def interrupted(signum, frame):
        if b.process is not None and b.process.poll() is None:
            os.killpg(b.process.pid, signal.SIGTERM)
        raise Blocked(f"interrupted by signal {signum}")
    signal.signal(signal.SIGTERM, interrupted)
    signal.signal(signal.SIGINT, interrupted)
    try:
        steps = (("source", b.reconstruct), ("toolchain", b.toolchain),
                 ("dependencies", b.dependencies), ("configure", b.configure), ("build", b.compile))
        for name, action in steps:
            action()
            if name == args.stop_after:
                if name == "build":
                    b.package()
                else:
                    b.data["status"] = "partial"
                    b.data["reason"] = f"Requested stop after {name}; no built artifact or runtime success claimed."
                break
        return 0
    except Blocked as exc:
        b.data["status"] = "blocked"
        b.data["reason"] = str(exc)
        return 1
    except BaseException as exc:
        b.data["status"] = "failed"
        b.data["reason"] = str(exc)
        b.data["traceback"] = traceback.format_exc()
        return 1
    finally:
        b.data["finished_utc"] = now()
        downloads = b.out / "downloads.jsonl"
        if downloads.exists():
            b.data["download_receipt"] = digest(downloads)
        b.save()
        print(json.dumps({"status": b.data["status"], "reason": b.data.get("reason"),
                          "receipt": str(b.out / "source-build.json")}), flush=True)


if __name__ == "__main__":
    raise SystemExit(main())
