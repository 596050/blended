# Exact checkpoint publication

The reviewed checkpoint `88f5a032ca4fcd26f75ca5f72de27373c27af4db`, tree
`b907c8c8962beab41b17a779e54412da5f4c015f`, was published to
`596050/blended`, branch `parity/upstream-browser-ports`.

The first import run, `39978987710`, verified the exact bundle and then failed
because GitHub did not yet have the original startup asset referenced by a
preserved Git LFS pointer. It left the target branch unchanged. The original
121,384-byte asset was supplied with its verified upstream SHA256; neither the
target checkpoint nor the pointer was modified.

The second run, `39981104052`, successfully uploaded that one object and
published the exact commit with an explicit expected-base lease. A separate
public `git ls-remote` query and GitHub Git commit/tree query confirmed the
result. Both attempts, their raw command outputs, and the successful importer
inputs are retained here. `summary.json` binds the important identities.

Publication establishes availability of the exact source and evidence checkpoint.
It runs zero Blender cases and does not change any test or feature parity gate.

- [Original failed import](https://github.com/596050/blended/actions/runs/39978987710)
- [Successful import](https://github.com/596050/blended/actions/runs/39981104052)
- [Published checkpoint](https://github.com/596050/blended/commit/88f5a032ca4fcd26f75ca5f72de27373c27af4db)
