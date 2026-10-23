# Final dependency and cache infrastructure regressions

The complete infrastructure discovery command ran **346 tests with zero skips**
and returned exit code 0. Unittest reported 121.485 seconds. Before and after
hashes match for all 156 selected implementation, workflow, patch, cache-contract
and original-preimage files.

`capture.py` recorded inputs before launching the actual process. `execution.json`
binds its raw stdout/stderr, exact command, timing, return code, interpreter,
CMake executable, capture tool and both input inventories. The recorded Git HEAD
predates these uncommitted implementation changes; the individual file identities
and working-tree status identify the tested inputs.

The command was:

```bash
env BLENDED_INVENTORY_CMAKE=/workspace/scratch/d63596d831b2/runtime/browser-python/bin/cmake \
  python3 -m unittest discover -s tests -q
```

This rerun includes nine additional cache failure regressions after the preceding
337-test run. Restored dependencies require the independently preserved regular
file manifest and the exact three PNG aliases derived from the original
installer. Missing, additional, redirected, cyclic or otherwise altered aliases
cannot qualify a cache. The actual restored key must also match, and errors
produce a final failed receipt. New candidate caches are never restored merely
because an input-hash prefix matches.

`workflow-static-validation.json` separately records successful YAML parsing,
AST parsing of all five embedded Python bodies, the exact cache selection policy
and both frozen original-invocation plan hashes. It is a static check, not a
GitHub Actions execution.

Raw output includes expected failures emitted by negative-test fixtures. The
outer unittest process, preserved final summary and actual exit code determine
the infrastructure result. Prior evidence is unchanged.

**These are infrastructure regressions. They execute no newly qualified original
Blender browser cases and do not change the 516 strict-pair result or establish
full feature parity.**
