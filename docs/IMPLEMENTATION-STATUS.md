# Implementation status, 23 October 2026

## Latest verified compatibility batch

131 Blender runtime cases / 1,049 assertion events pass in native Rust and the actual deployed browser. Original C++ assertion transcripts independently match native Rust and Chromium WASM without floating differences requiring tolerance allowance. Reference: `94363991e7dcf39e2d70614aa002ab6f67764a5d`; verified runtime source: `2c7abe637e8eca6ea8937c871f406fa6ac123006`; run: `39918173966`.

The new 32 cases cover four complete collection test files and preserve 170 assertion sites / 521 runtime events. The signed-zero vector hash compile-time assertion is now ported, positively compiled and mutation-tested on native and WASM targets. It is not counted among runtime cases. Total native Rust runtime tests: 144, consisting of 131 Blender, three Cycles, six product geometry and four safety tests.

Corrected inventory source `986ac6ffc6892e5e3738d7e281da9413cf453914`, run `39918761201`, verifies 132 mapped source identities against the exact checkout. The heuristic candidate count increased to 5,673 after C++ numeric separators stopped hiding declarations. There are 5,541 unmapped source candidates. None of these counts establishes a complete runtime denominator.

## Working modeller and failed renderer remain separate

The repository's prominent launch link opens the previously verified Rust/Three.js modeller at source `25e641c0d311f61c473755d1c7ee821289a27d15`, static commit `15752e8b7c31cc1ea3aa4ec32ab7457b0736ab38`. Its public-URL workflow `39860686907` passed the limited editing/rendering/interchange acceptance checks. The modeller's existing button retains the 17-case ABI; the separate conformance workbench executes all 131 runtime ports. New test-library additions are not new modelling features.

The Solarxy-derived application compiled, and selected existing suites previously passed, but actual browser rendering failed with blank imported geometry and some GPU-device-loss/panic runs. That failure remains unresolved in issue #1 and `deployment-evidence`. The working Three.js modeller does not inherit Solarxy's procedural editor or turn the failed experiment into a pass.

## Full-parity work remains incomplete

The full-completeness CI job remains failed. Broad native runtime enumeration, the remaining test ports, executing fixture-based application workflows and Blender-compatible rendering are unfinished. This includes mesh/BMesh editing, modifiers, sculpting, Geometry Nodes, animation, rigging, physics, compositor, video editor, Python/add-on API and .blend serialisation. There is no claimed full Blender/Cycles/EEVEE parity.

Original native BLI discovery retained 1,644 registrations and the duplicate stack.Peek identity; it is not all Blender tests and not a count of ported/passing tests. The prior tests/files LFS hash verification covered 6,691 objects, not every possible dependency or execution job.

See `COMPLETE-TEST-PORT.md`, `ASSERTION-FIDELITY.md`, `COLLECTION-PORT-VERIFICATION.md` and the machine-readable status/evidence files. Do not remove failing, missing, blocked or unsupported work from the completion criteria.
