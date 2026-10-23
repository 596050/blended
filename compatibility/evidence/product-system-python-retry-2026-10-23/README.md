# Original system-Python CTest dependency retry

The original `script_validate_on_system_python` registration at Blender commit
`94363991e7dcf39e2d70614aa002ab6f67764a5d` **passed** after its missing `setuptools`
dependency was supplied privately. CTest returned zero, and its JUnit output
records exactly one executed driver with no failure, error, or skip. This is one
native CTest driver result. No internal leaf-case count or browser pass is inferred.

## Preserved first attempt

The original failure remains unchanged in
`../product-expanded-config-2026-10-23/system-python-execution.json`,
`system-python.log`, and `system-python-junit.xml`. The original driver attempted
to import `build_files/utils/make_bpy_wheel.py` and received
`ModuleNotFoundError: No module named 'setuptools'`. CTest returned 8.

The retry receipt binds all three prior files by hash. No prior result was replaced.

## Exact dependencies and interpreter

Two official Ubuntu Noble packages were downloaded through the existing private,
authenticated APT configuration and extracted beneath
`runtime/product-system-python-deps/root`:

| Package | Version | Archive bytes | SHA-256 |
| --- | --- | ---: | --- |
| `python3-setuptools` | `68.1.2-2ubuntu1.2` | 396,614 | `27ede03d8c5046c30cf1dcdc8835708408d27bdd3561e881b5d66656e6ff23e7` |
| `python3-pkg-resources` | `68.1.2-2ubuntu1.2` | 167,914 | `13caaa69d5ba8b02e90087d4bcef714c0581e591e820804d15d12f582055147a` |

`dependency-packages.json` retains package versions, archive identities, exact
authenticated metadata, extraction results, and the unchanged host package-status
identity. `extracted-package-files.json` records the extracted file hashes. No
global package installation occurred.

The test still used **`/usr/bin/python3.12`**, observed as Python 3.12.3. Its
8,025,024-byte executable has SHA-256
`a92f0f95e883390c7256b2e441484aac06b1002dbe1d924141a77c8d82f96223`.
The separate interpreter observation confirms that both dependency imports came
from the declared private prefix and that setuptools reports version 68.1.2.

The only added environment setting was:

```text
PYTHONPATH=/workspace/scratch/d63596d831b2/runtime/product-system-python-deps/root/usr/lib/python3/dist-packages
```

The previous configuration's library and pkg-config environment was retained.
The original test script, interpreter, registered command, configuration name,
working directory, and CTest environment properties were rechecked. The CTest
wrapper's `--output-junit` destination changed to this new evidence directory to
preserve the first attempt. No original source, assertion, selector, or tolerance
was changed.

## Evidence

| Artifact | Bytes | SHA-256 |
| --- | ---: | --- |
| `system-python-execution.json` | 8,105 | `dfdec2b7b2d2d89902bb0250ee2716a12d5d6167f49e1bc026b78ffd458b4fd1` |
| `dependency-packages.json` | 6,143 | `b2257869a43e8d4c0c28a74cba6ad1dfaf2f736f278d9714fa47144d9fcc819e` |
| `system-python.log` | 277 | `c761f1697c852b24204ee05092441326d5f1f25e520e2e3587c2207bc651ef75` |
| `system-python-junit.xml` | 396 | `3f1835eaf5cf995c405efd89a41cf3adda5a612dac5e9d5e375d483f8edd6595` |
| `interpreter.stdout.json` | 1,215 | `5a52a2ba086b23031073af44a7d834a9f0cdbba3131f12097a06292b0a139d79` |
| `selected-ctest.json` | 1,594 | `f4913cc98f2c89babf49fbef0e52d68c1b61cc063bad0bec9f23abd201b0e0d8` |

`prepare-dependencies.py`, `observe-interpreter.py`, and `run-system-python.py`
preserve the exact operations. Their receipts bind the executed script bytes and
commands. Reproduction must use new evidence destinations and retain the same
source pin, interpreter identity, original registration, and package versions.

The receipt keeps `runtime_leaf_enumeration_complete`, `browser_parity`, and
`full_feature_parity` false. The original driver checks importability of its own
upstream-selected tool scripts; this execution does not invent a count for those
imports or promote them to independently discovered tests.
