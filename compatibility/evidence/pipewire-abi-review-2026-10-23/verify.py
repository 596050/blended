"""Independently inspect the exact local PipeWire package closure; do not install it."""
from datetime import datetime, timezone
import hashlib
import io
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import sys
import tarfile


directory = Path(__file__).resolve().parent
repo = directory.parents[2]
workspace = repo.parent
output = directory / "report.json"
if output.exists():
    raise RuntimeError("immutable audit already exists")
receipt_path = repo / "compatibility/evidence/product-configure-2026-10-23/host-dependency-packages.json"
receipt = json.loads(receipt_path.read_text())
prefix = workspace / "runtime/product-host-deps/root"
versions = {
    "libpipewire-0.3-0t64": "1.4.7-3ubuntu2",
    "libpipewire-0.3-dev": "1.4.7-3ubuntu2",
    "libspa-0.2-dev": "1.4.7-3ubuntu2",
    "libspa-0.2-modules": "1.4.7-3ubuntu2",
    "libwebrtc-audio-processing-1-3": "1.3-3build1",
    "libabsl20240722": "20240722.0-4ubuntu1",
}


def identity(path):
    data = path.read_bytes()
    return {"path": str(path), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


environment = dict(os.environ)
overrides = {
    "LD_LIBRARY_PATH": str(workspace / "runtime/gcc-14/root/usr/lib/x86_64-linux-gnu") + ":" + str(prefix / "usr/lib/x86_64-linux-gnu"),
    "PKG_CONFIG_SYSROOT_DIR": str(prefix),
    "PKG_CONFIG_LIBDIR": str(prefix / "usr/lib/x86_64-linux-gnu/pkgconfig") + ":" + str(prefix / "usr/share/pkgconfig"),
}
environment.update(overrides)


def run(command):
    process = subprocess.run(command, env=environment, capture_output=True, text=True, timeout=30)
    return {"command": command, "returncode": process.returncode, "stdout": process.stdout, "stderr": process.stderr}


records = []
elf_records = []
for package, expected_version in versions.items():
    recorded = next(row for row in receipt["packages"] if row["package"] == package)
    path = Path(recorded["path"])
    actual = identity(path)
    assert actual["sha256"] == recorded["sha256"] == recorded["authenticated_sha256"]
    assert actual["bytes"] == recorded["bytes"]
    actual_version = subprocess.check_output(["dpkg-deb", "-f", str(path), "Version"], text=True).strip()
    assert actual_version == expected_version == recorded["version"]
    records.append({**actual, "package": package, "version": actual_version,
                    "official_archive_path": recorded["official_archive_path"], "depends": recorded["depends"]})
    archive_bytes = subprocess.check_output(["dpkg-deb", "--fsys-tarfile", str(path)])
    with tarfile.open(fileobj=io.BytesIO(archive_bytes), mode="r:") as archive:
        for member in archive:
            if not member.isfile():
                continue
            data = archive.extractfile(member).read()
            if data[:4] != b"\x7fELF":
                continue
            relative = member.name.removeprefix("./")
            extracted = prefix / relative
            assert extracted.read_bytes() == data
            dynamic = subprocess.check_output(["readelf", "-d", str(extracted)], text=True)
            symbols = subprocess.check_output(["readelf", "-V", str(extracted)], text=True)
            required = sorted(set(re.findall(r"\b(?:GLIBC|GLIBCXX|CXXABI)_[0-9.]+", symbols)))
            child = run([sys.executable, "-c", "import ctypes,sys; ctypes.CDLL(sys.argv[1]); print('loaded')", str(extracted)])
            elf_records.append({"package": package, **identity(extracted), "archive_member": relative,
                                "needed": re.findall(r"\(NEEDED\)\s+Shared library: \[([^]]+)\]", dynamic),
                                "required_symbol_versions": required, "runtime_load": child})

pkg_config = str(prefix / "usr/bin/pkgconf")
checks = [run([pkg_config, "--atleast-version=1.1.0", "libpipewire-0.3"]),
          run([pkg_config, "--modversion", "libpipewire-0.3"]),
          run([pkg_config, "--cflags", "--libs", "libpipewire-0.3"]),
          run([sys.executable, "-c", "import ctypes,sys; p=ctypes.CDLL(sys.argv[1]); p.pw_get_library_version.restype=ctypes.c_char_p; print(p.pw_get_library_version().decode())",
               str(prefix / "usr/lib/x86_64-linux-gnu/libpipewire-0.3.so.0.1407.0")])]
glibc_requirements = {v for row in elf_records for v in row["required_symbol_versions"] if v.startswith("GLIBC_")}
max_glibc = max(glibc_requirements, key=lambda value: tuple(map(int, value.removeprefix("GLIBC_").split("."))))
passed = all(row["runtime_load"]["returncode"] == 0 for row in elf_records) and all(row["returncode"] == 0 for row in checks)
report = {
    "schema": 1,
    "purpose": "independent ABI and exact-package review for the unchanged Blender PipeWire >=1.1.0 requirement",
    "created_utc": datetime.now(timezone.utc).isoformat(),
    "verifier": identity(Path(__file__)),
    "authenticated_package_receipt": identity(receipt_path),
    "host_glibc": platform.libc_ver(),
    "host_libc": identity(Path("/lib/x86_64-linux-gnu/libc.so.6")),
    "host_package_status": identity(Path("/var/lib/dpkg/status")),
    "environment_overrides": overrides,
    "packages": records,
    "elf_count": len(elf_records),
    "maximum_required_glibc": max_glibc,
    "elfs": elf_records,
    "checks": checks,
    "status": "compatible_library_closure" if passed else "requires_review",
    "host_package_installations": 0,
    "blender_flags_changed": False,
    "tests_executed": 0,
    "limitations": ["No audio daemon or device test was performed.",
                    "This is dependency and ABI evidence, not a Blender build or parity pass.",
                    "The isolated extraction uses selected official Questing packages on a Noble host; it is not a Noble backport."],
}
output.write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps({"status": report["status"], "elf_count": len(elf_records), "maximum_required_glibc": max_glibc,
                  "failed_loads": [{"path": row["path"], "stderr": row["runtime_load"]["stderr"]} for row in elf_records if row["runtime_load"]["returncode"]],
                  "checks": checks, "report": identity(output)}, indent=2))
raise SystemExit(0 if passed else 1)
