"""Record generated build graph and resource estimates without starting a build."""
from collections import defaultdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import shutil


evidence = Path(__file__).resolve().parent
repo = evidence.parents[2]
workspace = repo.parent
root = repo / "compatibility/evidence/product-native-gtest-2026-10-23"
output = root / "remaining-build-assessment.json"
if output.exists():
    raise RuntimeError("retain the original build assessment snapshot")
configuration_path = evidence / "configure-with-optix.json"
configuration = json.loads(configuration_path.read_text())
build = Path(configuration["command"][configuration["command"].index("-B") + 1])
makefile = build / "CMakeFiles/Makefile2"


def identity(path):
    data = path.read_bytes()
    return {"path": str(path), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


edges = defaultdict(set)
for line in makefile.read_text().splitlines():
    match = re.fullmatch(r"([^\s:]+\.dir/all): ([^\s:]+\.dir/all)", line)
    if match:
        edges[match[1]].add(match[2])
targets = {"cycles_test": "intern/cycles/test/CMakeFiles/cycles_test.dir",
           "blender_test": "tests/gtests/runner/CMakeFiles/blender_test.dir",
           "blender": "source/creator/CMakeFiles/blender.dir"}
object_files = sorted(build.rglob("*.o"))
object_bytes = sum(path.stat().st_size for path in object_files)
summary_path = root / "summary.json"
summary = json.loads(summary_path.read_text())
measured_seconds = sum(item["build_elapsed_seconds"] for item in summary["invocations"])
record = {"schema": 1, "created_utc": datetime.now(timezone.utc).isoformat(),
          "scope": "Build planning only; generated object rules are not test cases or runtime coverage.",
          "source_commit": configuration["source_commit"], "configuration_receipt": identity(configuration_path),
          "build_config": identity(build / "CMakeCache.txt"), "generated_makefile": identity(makefile),
          "completed_native_summary": identity(summary_path), "build_directory": str(build),
          "environment_overrides": configuration["environment_overrides"],
          "observed_resources": {"free_disk_bytes": shutil.disk_usage(build).free,
                                 "cgroup_memory_limit_bytes": int(Path("/sys/fs/cgroup/memory.max").read_text()),
                                 "cgroup_cpu_max": Path("/sys/fs/cgroup/cpu.max").read_text().strip(),
                                 "built_object_count": len(object_files), "built_object_logical_bytes": object_bytes,
                                 "completed_target_build_wall_seconds": measured_seconds,
                                 "completed_target_build_parallel_jobs": 2,
                                 "build_tree_logical_bytes": sum(path.stat().st_size for path in build.rglob("*") if path.is_file())},
          "targets": {}, "any_build_started_by_assessment": False, "tests_executed_by_assessment": 0}
for name, directory in targets.items():
    todo, closure = [directory + "/all"], set()
    while todo:
        node = todo.pop()
        if node in closure:
            continue
        closure.add(node)
        todo.extend(edges[node] - closure)
    rules, source_rules = set(), []
    for node in sorted(closure):
        path = build / node.removesuffix("/all") / "build.make"
        if path.is_file():
            rules.update(re.findall(r"^([^\s:]+\.o):", path.read_text(), re.M))
            source_rules.append(identity(path))
    existing = sorted(path for path in rules if (build / path).is_file())
    remaining = sorted(rules - set(existing))
    jobs = 1 if name == "cycles_test" else 2
    link = build / directory / "link.txt"
    record["targets"][name] = {
        "configured_dependency_target_count": len(closure), "configured_object_rule_count": len(rules),
        "existing_object_rule_count": len(existing), "remaining_object_rule_count": len(remaining),
        "dependency_directories": sorted(node.removesuffix("/all") for node in closure),
        "remaining_object_rules": remaining, "source_build_rules": source_rules,
        "link_command": {**identity(link), "content": link.read_text()},
        "suggested_command_not_executed": [str(workspace / "runtime/browser-python/bin/cmake"), "--build", str(build),
                                           "--target", name, "--parallel", str(jobs)],
        "suggested_parallel_jobs": jobs,
        "linear_wall_seconds_proxy_at_two_jobs": measured_seconds * len(remaining) / len(object_files),
        "linear_object_bytes_proxy": object_bytes * len(remaining) / len(object_files),
        "planning_wall_minutes_range": [20, 90] if name == "cycles_test" else [120, 360],
        "additional_disk_budget_gib_range": [2, 4] if name == "cycles_test" else [4, 10],
        "estimate_confidence": "low; unmeasured heavy template/kernel translation units, generated assets and link steps",
        "minimum_free_disk_reserve_bytes": 4 * 1024 ** 3,
        "initial_bounded_stage_seconds": 1200,
        "largest_compiler_or_link_peak_memory_bytes": None,
        "build_started": False,
    }
record["planning_caveats"] = [
    "The measured small-target throughput is a rough comparison, not a performance forecast for heavy Cycles kernels or application templates.",
    "The disk ranges are conservative working budgets, not measured requirements; retain a 4 GiB reserve and stop before exhausting it.",
    "The 8 GiB cgroup limit can still be exceeded by one heavy translation unit or the final link; single-job Cycles is the first proposed stage.",
    "Targets share dependencies, so their time and disk ranges must not be added as independent costs.",
    "A usable Blender runtime also needs packaging and runtime asset closure; compiling its executable alone does not qualify Python, UI or rendering tests.",
    "Source build flags, original tests and configuration remain unchanged. No command in this assessment was executed.",
]
output.write_text(json.dumps(record, indent=2) + "\n")
print(json.dumps({"assessment": identity(output), "resources": record["observed_resources"],
                  "targets": {name: {key: item[key] for key in
                    ("configured_dependency_target_count", "configured_object_rule_count", "existing_object_rule_count",
                     "remaining_object_rule_count", "linear_wall_seconds_proxy_at_two_jobs", "planning_wall_minutes_range")}
                              for name, item in record["targets"].items()}}, indent=2))
