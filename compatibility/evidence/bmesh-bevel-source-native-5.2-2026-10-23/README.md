# Original native bevel attempt under the restricted sandbox

This attempt loaded the exact original Blender 5.2 bevel fixture and executed
the unchanged `bevel_operator.py --run-all-tests` command with its original
helper. The source-derived registration and all inputs were bound before launch.

All 88 original case names produced explicit successful mesh comparisons and
validation results. The process then failed to exit after its log reported:

```text
pa_write() failed while trying to wake up the mainloop: Operation not permitted
```

The original 180-second guard terminated the process with return code -15 at
180.109222 seconds. `completed_successfully` is false. The observed pass markers
do not establish a completed invocation.

The raw receipt and log remain unchanged. The separately authorized retry is
under `../bmesh-bevel-source-native-elevated-5.2-2026-10-23/`; its summary compares
both attempts and retains this failure.

The first capture's unverified `/proc/<child-pid>` sample did not identify the
actual Blender process across the restricted PID namespace. The fields
`sampled_process_peak_rss_kib` and `sampled_process_peak_thread_count` must not be
used as Blender measurements. The independent kernel child-resource field
`child_max_rss_kib` reports 367,976 KiB and does not depend on that PID lookup.

Original source, helper, CMake context, preserved LFS pointer and exact payload
are included here. This attempt neither configured CTest nor ran a browser test.
