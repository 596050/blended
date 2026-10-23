"""Read-only supplementary RSS sampling using the mounted procfs PID namespace."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys
import time


directory = Path(__file__).resolve().parent
root_pid = int(sys.argv[1])
proc_root = Path("/proc") / str(root_pid)
samples_path = directory / "procfs-memory-samples.jsonl"
receipt_path = directory / "procfs-memory-observation.json"
if samples_path.exists() or receipt_path.exists():
    raise RuntimeError("retain original supplementary memory observation")
now = lambda: datetime.now(timezone.utc).isoformat()


def identity(path):
    raw = path.read_bytes()
    return {"path": str(path), "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def proc_fields(path):
    raw = (path / "stat").read_text()
    fields = raw[raw.rindex(")") + 2:].split()
    return {"pid": int(path.name), "parent": int(fields[1]), "group": int(fields[2]),
            "start_ticks": int(fields[19]), "rss_bytes": int(fields[21]) * os.sysconf("SC_PAGE_SIZE"),
            "command": raw[raw.index("(") + 1:raw.rindex(")")]}


bound_root = proc_fields(proc_root)
arguments = [argument.decode() for argument in (proc_root / "cmdline").read_bytes().split(b"\0") if argument]
expected_suffix = ["--build", "/workspace/scratch/d63596d831b2/runtime/product-native-configure-optix",
                   "--target", "cycles_test", "--parallel", "1"]
if arguments[1:] != expected_suffix or Path(arguments[0]).name != "cmake" or bound_root["group"] != root_pid:
    raise RuntimeError("procfs root is not the expected original Cycles CMake invocation")
parent = Path("/proc") / str(bound_root["parent"])
parent_arguments = [argument.decode() for argument in (parent / "cmdline").read_bytes().split(b"\0") if argument]
if not any(argument.endswith("product-native-cycles-2026-10-23/build-cycles.py") for argument in parent_arguments):
    raise RuntimeError("CMake parent is not the recorded bounded build wrapper")
namespace_fields = {key: value.strip() for key, value in
                    (line.split(":", 1) for line in (proc_root / "status").read_text().splitlines()
                     if line.startswith(("NSpid:", "NSpgid:", "NSsid:")))}
record = {"schema": 1, "started_utc": now(), "procfs_root": bound_root,
          "actual_arguments": arguments, "bound_parent_arguments": parent_arguments,
          "namespace_fields": namespace_fields, "observer": identity(Path(__file__)),
          "read_only": True, "sampling_interval_seconds": 2, "maximum_elapsed_seconds": 1200,
          "scope": "Supplementary sampled process-group RSS after namespace mapping; not a full-duration peak or memory guard.",
          "earlier_process_group_rss_fields": "Unreliable: original wrapper compared namespace-local Popen PID to outer procfs group IDs. Cgroup metrics remain valid.",
          "processes_signalled": 0, "tests_executed": 0}
started = time.monotonic()
peak, samples = 0, 0
reason = "time_bound"
with samples_path.open("x") as stream:
    while time.monotonic() - started < record["maximum_elapsed_seconds"]:
        try:
            current = proc_fields(proc_root)
            if current["start_ticks"] != bound_root["start_ticks"]:
                reason = "bound_process_identity_changed"
                break
        except (FileNotFoundError, ProcessLookupError):
            reason = "bound_process_exited"
            break
        members = []
        for path in Path("/proc").iterdir():
            if not path.name.isdigit():
                continue
            try:
                observed = proc_fields(path)
                if observed["group"] == root_pid:
                    members.append(observed)
            except (OSError, ValueError, IndexError):
                continue
        rss = sum(member["rss_bytes"] for member in members)
        peak = max(peak, rss)
        sample = {"time_utc": now(), "process_group_rss_bytes": rss, "members": members}
        stream.write(json.dumps(sample, sort_keys=True) + "\n")
        stream.flush()
        samples += 1
        time.sleep(2)
record.update(finished_utc=now(), elapsed_seconds=time.monotonic() - started, stop_reason=reason,
              sample_count=samples, peak_sampled_group_rss_bytes=peak, samples=identity(samples_path))
with receipt_path.open("x") as stream:
    json.dump(record, stream, indent=2)
    stream.write("\n")
print(json.dumps({key: record[key] for key in ("stop_reason", "sample_count", "peak_sampled_group_rss_bytes")}))
