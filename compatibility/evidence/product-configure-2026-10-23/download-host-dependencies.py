"""Download verified official host development packages into an isolated prefix."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess


evidence = Path(__file__).resolve().parent
workspace = evidence.parents[2].parent
prefix = workspace / "runtime/product-host-deps"
apt_root = prefix / "apt"
destination = prefix / "root"
receipt_path = evidence / "host-dependency-packages.json"
if receipt_path.exists() or destination.exists():
    raise RuntimeError("dependency output already exists; retain immutable attempts")
destination.mkdir()
environment = dict(os.environ)
environment["APT_CONFIG"] = str(apt_root / "apt.conf")
packages = [
    "pkgconf", "libjack-jackd2-dev", "libpulse-dev", "libdbus-1-dev", "libxkbcommon-dev",
    "libx11-dev", "libxi-dev", "libxfixes-dev", "libxrender-dev",
    "libpipewire-0.3-dev=1.4.7-3ubuntu2", "libpipewire-0.3-0t64=1.4.7-3ubuntu2",
    "libspa-0.2-dev=1.4.7-3ubuntu2", "libspa-0.2-modules=1.4.7-3ubuntu2",
    # Explicit runtime packages close the development packages' relative library symlinks.
    "libjack-jackd2-0", "libpulse0", "libdbus-1-3", "libxkbcommon0", "libxi6", "libxfixes3",
    "libxrender1", "libxext6", "libxcb1", "libxau6", "libxdmcp6",
]
now = lambda: datetime.now(timezone.utc).isoformat()


def identity(path):
    data = path.read_bytes()
    return {"path": str(path), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


record = {"schema": 1, "purpose": "isolated host dependencies for exact Blender configuration",
          "started_utc": now(), "requested_packages": packages, "stages": [], "packages": [],
          "environment_overrides": {"APT_CONFIG": str(apt_root / "apt.conf")},
          "package_index_receipt": identity(evidence / "host-package-index.json"),
          "host_package_status_before": identity(Path("/var/lib/dpkg/status")),
          "extraction_root": str(destination), "host_package_installations": 0,
          "tests_executed": 0, "status": "pending"}


def persist():
    receipt_path.write_text(json.dumps(record, indent=2) + "\n")


def stage(name, command):
    log_path = evidence / ("host-dependency-" + name + ".log")
    if log_path.exists():
        raise RuntimeError("stage output already exists")
    started = now()
    with log_path.open("wb") as log:
        process = subprocess.run(command, env=environment, cwd=prefix, stdout=log, stderr=subprocess.STDOUT)
    record["stages"].append({"name": name, "command": command, "started_utc": started,
                             "finished_utc": now(), "returncode": process.returncode, "log": identity(log_path)})
    persist()
    if process.returncode:
        raise RuntimeError("stage failed: " + name)


try:
    options = ["--no-install-recommends", "--no-install-suggests", "--reinstall"]
    stage("plan", ["/usr/bin/apt-get", "--simulate", *options, "install", *packages])
    stage("uris", ["/usr/bin/apt-get", "--print-uris", "--download-only", *options, "install", *packages])
    stage("download", ["/usr/bin/apt-get", "--yes", "--download-only", *options, "install", *packages])
    for archive in sorted((apt_root / "cache/archives").glob("*.deb")):
        fields = subprocess.check_output(["dpkg-deb", "--field", str(archive),
                                          "Package", "Version", "Architecture"], text=True)
        control = dict(line.split(": ", 1) for line in fields.splitlines() if ": " in line)
        spec = control["Package"] + "=" + control["Version"]
        metadata = subprocess.check_output(["/usr/bin/apt-cache", "show", spec], env=environment, text=True)
        candidates = []
        for paragraph in metadata.split("\n\n"):
            stanza = dict(line.split(": ", 1) for line in paragraph.splitlines()
                          if line and not line.startswith(" ") and ": " in line)
            if stanza.get("Package") == control["Package"] and stanza.get("Version") == control["Version"]:
                candidates.append(stanza)
        actual = identity(archive)
        matched = [stanza for stanza in candidates if stanza.get("SHA256") == actual["sha256"]
                   and int(stanza["Size"]) == actual["bytes"]]
        if not matched:
            raise RuntimeError("download did not match authenticated metadata: " + archive.name)
        source = matched[0]
        archive_record = {**actual, "package": control["Package"], "version": control["Version"],
                          "architecture": control["Architecture"], "authenticated_sha256": source["SHA256"],
                          "official_archive_path": source["Filename"], "depends": source.get("Depends", "")}
        process = subprocess.run(["dpkg-deb", "--extract", str(archive), str(destination)],
                                 stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        archive_record.update(extraction_returncode=process.returncode, extraction_output=process.stdout)
        record["packages"].append(archive_record)
        if process.returncode:
            raise RuntimeError("package extraction failed: " + archive.name)
    if not record["packages"]:
        raise RuntimeError("no dependency packages were downloaded")
    record["status"] = "verified_extracted"
except Exception as error:
    record["status"] = "failed"
    record["error"] = str(error)
    raise
finally:
    record.update(finished_utc=now(), host_package_status_after=identity(Path("/var/lib/dpkg/status")))
    persist()
    print(json.dumps({"status": record["status"], "verified_packages": len(record["packages"]),
                      "host_package_installations": 0, "tests_executed": 0}))
