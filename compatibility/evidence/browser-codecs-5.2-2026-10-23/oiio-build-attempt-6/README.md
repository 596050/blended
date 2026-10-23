# Completed OIIO integration build

This attempt finished successfully after the earlier completed summary was frozen. The prior summary remains unchanged. This entire attempt is now immutable and can be appended to a subsequent checkpoint.

[execution.json](execution.json) records the actual process outcomes: exact final patch application followed by 21 dependency recipes, all exit 0 with no timeout. The final selected manifest is SHA256 `b2881dbf9366a9e1ad6bbf9ffe4d61b0b53d47745472bd2b14f02da5730f2708`. The actual recipe durations sum to 1,832.200760 seconds at one compile job, including 466.232883 seconds for OIIO.

[completion-summary.json](completion-summary.json) validates the completed receipts and logs, verifies the installed library and recipe hashes, and binds the preserved generated configuration. It is a summary of those executions, not another test run. Its reproducible observer is [freeze-completion.py](freeze-completion.py).

The real linked Node/Wasm smoke constructed both readers and writers for WebP, JPEG2000, HEIF and DPX; required AV1 encoder and decoder availability; and checked the existing physical-memory implementation. The raw output is in [openimageio.log](openimageio.log). The successful set-e recipe after its `node` command provides completion evidence; there is no invented separately instrumented Node process receipt.

The exact installed [openimageio-CMakeCache.txt](openimageio-CMakeCache.txt) is 38,421 bytes, SHA256 `fb61e9fcbe52833cc22ca08a788f08b262828ee6ea51ac94b94f51762975a53c`. It records `USE_WEBP=ON`, `USE_OPENJPEG=ON`, `USE_LIBHEIF=ON`, `EMBEDPLUGINS=ON`, and `BUILD_SHARED_LIBS=OFF`. The original static OIIO package exports are preserved beside it.

This result executes **zero original Blender cases** and earns **zero browser application passes**. It validates the dependency integration. The rebuilt Blender browser still must execute the unchanged 80 original ImBuf parent IDs and 57 native subtest IDs with their original assertions and tolerances. CINEON is enabled in the selected Blender configuration; its actual Blender implementation remains part of that application gate.
