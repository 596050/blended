"""Explicit reviewed contract shards, never optional or discovered by a glob.

The historical lock file remains byte-for-byte unchanged. New families use
small independently reviewed shards, and every consumer reads the same union.
"""
from pathlib import Path
import json
EXTENSIONS=("compatibility/polyfill-assertion-contract.lock.json","compatibility/span-assertion-contract.lock.json","compatibility/mask-expression-assertion-contract.lock.json","compatibility/container-view-assertion-contract.lock.json","compatibility/callable-utility-assertion-contract.lock.json")
def load_contracts(root:Path)->dict:
    base=json.loads((root/"compatibility/assertion-contracts.lock.json").read_text())
    if base.get("schema")!=1 or not base.get("contracts"):raise ValueError("Invalid base contracts")
    merged=dict(base);merged["contracts"]=list(base["contracts"])
    for name in EXTENSIONS:
        shard=json.loads((root/name).read_text())
        if shard.get("schema")!=1 or shard.get("reference_commit")!=base["reference_commit"] or not shard.get("contracts"):
            raise ValueError("Missing or mismatched required contract shard: "+name)
        merged["contracts"].extend(shard["contracts"])
    seen=set()
    for contract in merged["contracts"]:
        for identity in contract["case_ids"]:
            key=(contract["source_path"],identity)
            if key in seen:raise ValueError("Duplicate reviewed source identity: "+str(key))
            seen.add(key)
    return merged
