# Independent review of the production DPX correction

The source review found no material blocker in the reviewed production integration. This directory preserves the exact reviewed inputs, the verification method and the measured results. It records no Blender test pass, decoder success or parity credit.

The initial review used actual source reads and an in-memory patch comparison. `verify-source-contract.py` then repeated the source checks while saving this record. Its fresh start and completion timestamps are in `report.json`; no earlier timestamps or missing process receipts have been reconstructed. The script read files, inspected existing Git objects, interpreted patch hunks in memory and wrote only this new review directory. It did not compile or run the regressions, Wasm programs or Blender.

## Source change

The original `DPXColorConverter.cpp` and `DPXHeader.h` test preimages were compared byte for byte with the pinned OpenImageIO 3.1.13.1 archive. The complete archive was hashed as:

`0fc59b8e2708ded02d3793b8f3331f037ed49bfcde38158f05ac0e876ebb85b7`

The production patch changes only the active return expressions at source lines 301 and 309:

```cpp
return -int64_t(pixels) * 3 * int64_t(bytes);
return -int64_t(pixels) * 4 * int64_t(bytes);
```

Converting both unsigned operands before multiplication preserves signed arithmetic for the negative storage sentinel. The inactive later implementation and every other source byte remain unchanged.

The 302-byte production patch and the retained 716-byte diagnostic patch were independently interpreted against the same exact original file. Both produced identical corrected source, SHA-256:

`28dd63ce548ee759f09bd23c2a90040408e3f91ffdfc7be3888fb357ad11d9b3`

The source preimage is:

`793e53edfac8dc79b8cea7bf0cc15c29a23b947e5559cf65cbe4bafd7227ebf1`

The shorter patch encodes the same two edits without context lines. Its different patch-file hash does not represent a different corrected source. The retained diagnostic patch comes from the explicitly labeled recovery record; its bytes match the digest recorded before workspace maintenance.

## Manifest and recipe checks

The selected codec manifest hashes to:

`1c98842c68dc7706630ce31132cdab20649ea61b860dd05b88722dc1a79b0bcf`

Both the build driver and runtime probe select this exact value. The outer patch, its application helper, the inner DPX patch and both source test preimages match their declared byte lengths and hashes.

All 11 outer patch outputs were reconstructed in memory from the retained original port preimages. Each resulting length and hash equals the selected manifest. Compared with the patch in base commit `9e75e19fbddf80ab68e60c4a7edefd8cd6e3c20c`, only these generated outputs change:

- `scripts/deps/openimageio.sh`
- `scripts/deps/openimageio-dpx-signed-buffer.patch`

The generated CMake files, other dependency recipes, required Blender and OIIO feature flags, dependency versions and dependency insertion order remain unchanged. The recipe checks the original source and inner patch hashes before `patch --batch --fuzz=0`, then checks the exact corrected source hash before configuration and compilation.

The existing unconditional OIIO rebuild remains in place. An old installed configuration marker cannot bypass this recipe. The outer `git apply --whitespace=error-all` guard remains unchanged. The application inventory includes both the changed recipe and the delivered inner patch.

## Regression design review

The new component regressions extract the actual upstream helper body and descriptor enum from the verified source files. They compile before and after variants under explicit unsigned 32-bit and 64-bit aliases for `size_t`, request undefined-behavior sanitization, and compare results with a signed mathematical expectation.

Source inspection confirmed coverage of the concrete 32 by 32 RGBA8 arithmetic, all five descriptor branches using the negative sentinel expressions, positive-size and unsupported-descriptor results, exact preservation of the inactive source, and rejection of changed source or patch bytes before source mutation. The declared parameter sets contain 120 negative-branch combinations and 380 positive/default combinations. These are counts of inputs described by the regression source, not execution results measured by this review.

The parent agent reported that its separate direct regression run completed 15 tests with zero failures, exit 0 and an elapsed time of 1.348 seconds. That result was communicated in a collaboration message. This reviewer did not execute that run or independently inspect its raw receipt, so it is recorded only as a parent-reported result.

## Evidence and limits

`inputs/current` contains byte-preserving snapshots of the reviewed package files, selectors and workflow. `inputs/original-port` contains the three existing port preimages used by the outer patch. `inputs/base-commit` contains the earlier manifest and patch read from the exact base Git commit. `inputs/prior-diagnostic` contains the verified earlier patch encoding. `report.json` binds these snapshots to the paths and identities read during this review and includes the source and recipe differences.

The full upstream archive was hashed and its relevant members compared, but the 55 MB archive is not duplicated in this review directory. Its exact retained source members and archive identity are recorded. The review method and all saved files are bound by the final inventory.

This establishes source and recipe consistency. The integer-width models do not establish a Wasm ABI result or successful DPX decoding. The interrupted standalone controlled comparison has no observed modified-library runtime result. A fresh full source build and complete original ImBuf invocation are still required before changing any original-suite qualification. This review changes no original tests, expected results, thresholds or selectors and awards zero qualification credit.
