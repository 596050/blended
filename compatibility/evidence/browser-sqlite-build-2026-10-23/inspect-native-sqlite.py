import json, sqlite3, _sqlite3, sys
c = sqlite3.connect(":memory:")
print(json.dumps({"python":sys.version,"sqlite_version":sqlite3.sqlite_version,"sqlite_module_file":getattr(_sqlite3,"__file__",None),"compile_options":[row[0] for row in c.execute("PRAGMA compile_options")],"original_blender_tests_executed":False},indent=2))
c.close()
