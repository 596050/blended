# Next original Blender 5.2 invocations: bounded source audit

`proposed-next-invocations.json` retains and authenticates all 101 unexpanded
declarations in the frozen 132-declaration source plan. It provides detailed
original commands, driver semantics, source bindings, fixture identities and
prerequisites for eight CPU-oriented candidates. It does not modify the frozen
plan, configure CTest, execute tests or claim native/browser passes.

| Priority | Original registration | Useful coverage | Available input |
| --- | --- | --- | --- |
| 1 | `bmesh_bevel` | 88 literal mesh regression specifications | Exact 2,387,547-byte original fixture already cached |
| 2 | `operators` | 105 literal mesh operator regression specifications | Exact 4,028,858-byte original fixture already cached |
| 3 | `bl_node_group_interface` | Socket types, panels, ordering and iteration across geometry, shader and compositor node systems | Exact 79,690-byte original empty scene already cached |
| 4 | `constraints` | Object/bone transforms, action slots and geometry-attribute constraints | Exact 933,385-byte original fixture already cached |
| 5 | `mesh_join` | Materials, shape keys, face sets and shared object data | Generated meshes; no external fixture required by the script |
| 6 | `blendfile_io` | Full and partial saves, reopening, runtime IDs and linking | Generated data; requires a private writable output directory |
| 7 | `node_tools` | Geometry-node tools and object inputs | Generated meshes and node graphs |
| 8 | `sequencer_strip_naming` | Exact duplicate naming rules for meta strips | Generated metadata; no media file required |

The listed specification and source-method counts are static observations, not
runtime leaf inventories. Native execution must establish the actual identities,
outcomes, subtests and process completion. Conditional entries remain conditional;
the existing unittest adapter's rejection cannot be bypassed by changing their
registration text or the frozen plan.

The fixture payloads were accepted only after matching the SHA-256 and size in
the exact original 5.2 archive's LFS pointers. Their current cached location in a
newer product source tree gives them no authority by itself. The audit did not
materialize, download or modify those resources.

The original mesh driver has two particularly important controls:
`--run-all-tests` enables comparison, while `--run-test` disables comparison for
visual inspection; `BLENDER_TEST_UPDATE` can rewrite golden objects. Future
qualification must retain the full original command and keep update mode absent.

All 101 declarations remain in the audit, including six helper-function
declarations, generated registrations, GPU/UI registrations, error-allowing
drivers and a disabled experimental script reference absent from the pinned
archive. These are not 101 known leaf cases or a configured CTest denominator.

After the audit identified the first candidate, the parent separately authorized
one bounded native bevel invocation and an environment retry. Their genuine
execution evidence is retained in the two `bmesh-bevel-source-native*` directories.
Those results are deliberately not imported into this proposal or the frozen
829-obligation browser ledger. No further suite was started.
