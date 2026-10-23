#!/usr/bin/env python3
"""Download an official historical package and measure its exact Chrome ELF."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tarfile
import urllib.request

OUT = Path(__file__).resolve().parent
URL = "https://dl.google.com/linux/chrome/deb/pool/main/g/google-chrome-stable/google-chrome-stable_155.0.8059.39-1_amd64.deb"
PACKAGE_BYTES = 143552428
EXPECTED_ELF = (297798984, "9bfb381296dffe75f3419d07b6cc64525105ed117d1453a4ef3b291cb97d2b58")


def now():
    return datetime.now(timezone.utc).isoformat()


def identity(path):
    with path.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    return {"path": str(path), "bytes": path.stat().st_size, "sha256": digest}


def write(name, value):
    with (OUT / name).open("x") as stream:
        stream.write(json.dumps(value, indent=2, sort_keys=True) + "\n")


started = now()
assert shutil.disk_usage(OUT).free > 4 * 1024 ** 3 + PACKAGE_BYTES + EXPECTED_ELF[0]
package = OUT / URL.rsplit("/", 1)[1]
assert not package.exists()
total = 0
with urllib.request.urlopen(URL, timeout=30) as response:
    status, resolved, headers = response.status, response.url, dict(response.headers)
    assert status == 200 and resolved == URL and int(headers["Content-Length"]) == PACKAGE_BYTES
    with package.open("xb") as stream:
        while chunk := response.read(1024 * 1024):
            total += len(chunk)
            assert total <= PACKAGE_BYTES
            stream.write(chunk)
assert total == PACKAGE_BYTES
download = {"schema": 1, "url": URL, "resolved_url": resolved, "status": status, "headers": headers,
    "started_utc": started, "finished_utc": now(), "artifact": identity(package),
    "authentication": "HTTPS from Google's official Linux package endpoint; current metadata advertises a different version.",
    "package_installed": False}
write("package-download.json", download)
control = subprocess.run(["dpkg-deb", "-f", str(package), "Package", "Version", "Architecture"],
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False, timeout=30)
assert control.returncode == 0
(OUT / "package-control.txt").write_bytes(control.stdout)
assert b"Package: google-chrome-stable\n" in control.stdout
assert b"Version: 155.0.8059.39-1\n" in control.stdout and b"Architecture: amd64\n" in control.stdout
binary = OUT / "chrome"
assert not binary.exists()
child = subprocess.Popen(["dpkg-deb", "--fsys-tarfile", str(package)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
matches = []
with tarfile.open(fileobj=child.stdout, mode="r|") as archive:
    for member in archive:
        if member.name in {"./opt/google/chrome/chrome", "opt/google/chrome/chrome"}:
            assert member.isfile() and member.size == EXPECTED_ELF[0] and not matches
            with archive.extractfile(member) as source, binary.open("xb") as destination:
                shutil.copyfileobj(source, destination, length=1024 * 1024)
            matches.append(member.name)
child.stdout.close()
stderr = child.stderr.read()
code = child.wait(timeout=30)
assert code == 0 and not stderr and len(matches) == 1
binary.chmod(0o555)
measured = identity(binary)
match = (measured["bytes"], measured["sha256"]) == EXPECTED_ELF
version = subprocess.run([str(binary), "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30, check=False)
(OUT / "version.stdout.log").write_bytes(version.stdout)
(OUT / "version.stderr.log").write_bytes(version.stderr)
receipt = {"schema": 1, "kind": "official-browser-binary-measurement", "started_utc": started,
    "finished_utc": now(), "measurement_tool": identity(Path(__file__)), "package": identity(package),
    "package_download": identity(OUT / "package-download.json"), "package_control": identity(OUT / "package-control.txt"),
    "member": matches[0], "binary": measured, "expected_ci_binary": {"bytes": EXPECTED_ELF[0], "sha256": EXPECTED_ELF[1]},
    "exact_ci_binary_match": match, "version_command": [str(binary), "--version"], "version_exit_code": version.returncode,
    "version_stdout": version.stdout.decode(errors="replace"), "version_stderr": version.stderr.decode(errors="replace"),
    "package_installed": False, "blender_tests_executed": 0,
    "scope": "An independently downloaded package's ELF matches the recorded CI binary identity; the CI process is not re-executed."}
write("measurement.json", receipt)
print(json.dumps({"receipt": identity(OUT / "measurement.json"), "exact_ci_binary_match": match,
                  "version_exit_code": version.returncode, "version_stdout": receipt["version_stdout"]}))
assert match and version.returncode == 0 and "155.0.8059.39" in receipt["version_stdout"]
