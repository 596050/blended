#!/usr/bin/env python3
"""One-time reviewed infrastructure edits for the full UTF8 stress transcript."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def replace(path,old,new):
    p=ROOT/path;s=p.read_text()
    if s.count(old)!=1:raise ValueError('Infrastructure baseline changed: '+path)
    p.write_text(s.replace(old,new))
def main():
    replace('tools/assertion_fidelity.py','try:report.update(compare(load_tape(a.reference),load_tape(a.port),expected,require_boundaries=True))','from fidelity_stream import compare_files\n        try:report.update(compare_files(a.reference,a.port,expected))')
    p=ROOT/'tools/assertion_fidelity.py';text=p.read_text();start=text.index('def browser(wasm:Path,output:Path):');end=text.index('\ndef main():',start)
    text=text[:start]+'def browser(wasm:Path,output:Path):\n    from fidelity_stream import browser_tape\n    return browser_tape(wasm,output)\n'+text[end:];p.write_text(text)
    replace('tools/fidelity/trace.rs','TAPE.with(|t|t.borrow().1.clone())','TAPE.with(|t|core::mem::take(&mut t.borrow_mut().1))')
    replace('.github/workflows/assertion-fidelity.yml','      - uses: actions/upload-artifact@v4\n        if: always()\n        with:\n          name: assertion-fidelity-comparisons','      - name: Preserve every assertion event in verified lossless compressed traces\n        if: always()\n        run: python3 tools/fidelity_stream.py evidence/fidelity\n      - uses: actions/upload-artifact@v4\n        if: always()\n        with:\n          name: assertion-fidelity-comparisons')
    replace('.github/workflows/test-port-conformance.yml',"'tools/assertion_fidelity.py',","'tools/assertion_fidelity.py', 'tools/fidelity_stream.py', 'tools/generate_utf8_tables.py', 'tools/verify_utf8_*.py',")
    replace('.github/workflows/test-port-conformance.yml','          python3 tools/fetch_upstreams.py blender\n          python3 - <<\'PY\'','          python3 tools/fetch_upstreams.py blender\n          python3 tools/generate_utf8_tables.py\n          python3 - <<\'PY\'')
    replace('.github/workflows/test-port-conformance.yml','permissions:\n  contents: read\njobs:','permissions:\n  contents: read\nconcurrency:\n  group: blender-conformance-${{ github.ref }}\n  cancel-in-progress: true\njobs:')
if __name__=='__main__':main()
