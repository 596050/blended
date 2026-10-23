"""Read authenticated official Ubuntu package indices without modifying host packages."""
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
receipt_path = evidence / "host-package-index.json"
log_path = evidence / "host-package-index.log"
if receipt_path.exists() or log_path.exists() or apt_root.exists():
    raise RuntimeError("package index output already exists; retain immutable attempts")
for directory in ("etc/apt.conf.d", "etc/sources.list.d", "etc/preferences.d", "state/lists/partial",
                  "cache/archives/partial", "log"):
    (apt_root / directory).mkdir(parents=True, exist_ok=True)

sources = apt_root / "etc/sources.list"
sources.write_text("""deb [signed-by=/usr/share/keyrings/ubuntu-archive-keyring.gpg] https://archive.ubuntu.com/ubuntu noble main universe
deb [signed-by=/usr/share/keyrings/ubuntu-archive-keyring.gpg] https://archive.ubuntu.com/ubuntu noble-updates main universe
deb [signed-by=/usr/share/keyrings/ubuntu-archive-keyring.gpg] https://archive.ubuntu.com/ubuntu noble-backports main universe
deb [signed-by=/usr/share/keyrings/ubuntu-archive-keyring.gpg] https://security.ubuntu.com/ubuntu noble-security main universe
deb [signed-by=/usr/share/keyrings/ubuntu-archive-keyring.gpg] https://archive.ubuntu.com/ubuntu questing main universe
""")
preferences = apt_root / "etc/preferences"
preferences.write_text("Package: *\nPin: release n=questing\nPin-Priority: 1\n")
configuration = apt_root / "apt.conf"
configuration.write_text(f'''Dir::Etc "{apt_root / 'etc'}";
Dir::Etc::main "apt.conf";
Dir::Etc::parts "apt.conf.d";
Dir::Etc::sourcelist "sources.list";
Dir::Etc::sourceparts "sources.list.d";
Dir::Etc::preferences "preferences";
Dir::Etc::preferencesparts "preferences.d";
Dir::State "{apt_root / 'state'}";
Dir::State::status "/var/lib/dpkg/status";
Dir::State::lists "lists";
Dir::Cache "{apt_root / 'cache'}";
Dir::Cache::archives "archives";
Dir::Log "{apt_root / 'log'}";
APT::Architecture "amd64";
APT::Sandbox::User "root";
Acquire::Languages "none";
Acquire::Retries "2";
Acquire::https::Timeout "30";
Acquire::AllowInsecureRepositories "false";
APT::Get::AllowUnauthenticated "false";
''')


def identity(path):
    data = path.read_bytes()
    return {"path": str(path), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


now = lambda: datetime.now(timezone.utc).isoformat()
environment = dict(os.environ)
environment["APT_CONFIG"] = str(configuration)
command = ["/usr/bin/apt-get", "update"]
record = {"schema": 1, "purpose": "isolated host dependency index for exact Blender configuration",
          "command": command, "environment_overrides": {"APT_CONFIG": str(configuration)},
          "started_utc": now(), "host_package_installations": 0, "tests_executed": 0,
          "source_configuration": identity(sources), "preferences": identity(preferences),
          "apt_configuration": identity(configuration),
          "trusted_keyring": identity(Path("/usr/share/keyrings/ubuntu-archive-keyring.gpg")),
          "host_package_status_before": identity(Path("/var/lib/dpkg/status"))}
with log_path.open("wb") as log:
    process = subprocess.run(command, env=environment, cwd=prefix, stdout=log, stderr=subprocess.STDOUT)
record.update(returncode=process.returncode, finished_utc=now(), log=identity(log_path),
              host_package_status_after=identity(Path("/var/lib/dpkg/status")),
              package_indices=[identity(path) for path in sorted((apt_root / "state/lists").iterdir())
                               if path.is_file() and path.name != "lock"])
receipt_path.write_text(json.dumps(record, indent=2) + "\n")
print(json.dumps({key: record[key] for key in ("returncode", "host_package_installations", "tests_executed")}))
print(log_path.read_text()[-6000:])
raise SystemExit(process.returncode)
