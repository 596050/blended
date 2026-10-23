/* Standalone CPython component entrypoint. This is not the Blender executable. */
#include <Python.h>
#include <sqlite3.h>
#include <stdio.h>

int main(int argc, char **argv)
{
  printf("BLENDED_SQLITE_COMPONENT sqlite=%s python=%s\n", sqlite3_libversion(), Py_GetVersion());
  fflush(stdout);
  const int result = Py_BytesMain(argc, argv);
  printf("BLENDED_SQLITE_COMPONENT_RETURN %d\n", result);
  fflush(stdout);
  return result;
}
