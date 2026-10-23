// Select the original test's documented verbose mode without filtering cases.
Module.arguments = ["/original/tests/python/bl_disk_file_hash_service_test.py", "--", "--verbose"];
Module.preRun = Module.preRun || [];
Module.preRun.push(function () {
  ENV.PYTHONHOME = "/usr/local";
  ENV.PYTHONPATH = "/original/scripts/modules";
  ENV.PYTHONDONTWRITEBYTECODE = "1";
  ENV.PYTHONUNBUFFERED = "1";
});
