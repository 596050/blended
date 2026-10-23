# Published-code CI validation

GitHub Actions run [39986612398](https://github.com/596050/blended/actions/runs/39986612398)
checked published commit `f25e69ed72fed2d31d7d65e657fd6515da4bd792`.

The infrastructure job ran **346 tests** and completed successfully in the
unittest-reported **109.674 seconds**. Its decoded original job log is retained
as `infrastructure-job.log`.

The Essentials evidence replay reproduced the current original-test report
byte-for-byte: SHA256
`d1b6df970fd0be756b374eba9ca2c662372106c9e3ec1fe6df9ea80bff553e81`.
The strict gate correctly exited 1 with **516 successful pairs**, **601 outcome
agreements**, and **829 obligations**. The gate remains blocked. This confirms
the retained evidence and gate behavior; it does not execute the Blender cases
again.

The downloaded Actions ZIP was checked against its API-provided byte count and
SHA256 before extracting `report.json` and `strict-gate.json`. Its metadata is
retained in `artifacts.json` and `summary.json`; the decoded original gate log
is `essentials-job.log`.

These two extracted reports are not a new standalone raw-evidence root. Their
unchanged referenced observations are retained in
`../unittest-parity-ledger-essentials-5.2-2026-10-23/`, and the complete downloaded
CI artifact preserves its own normalized raw files.

The separately running source build
[39986612484](https://github.com/596050/blended/actions/runs/39986612484)
must finish and qualify its new artifact before it can contribute new original
browser observations. Neither this CI replay nor the infrastructure count
increases Blender feature coverage.
