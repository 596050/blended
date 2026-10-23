cmake_minimum_required(VERSION 3.14)
project(RegistrationInventoryFixture NONE)
enable_testing()

# Standalone infrastructure fixture. These commands are not Blender tests.
add_test(NAME setup COMMAND "${CMAKE_COMMAND}" -E true)
set_tests_properties(setup PROPERTIES FIXTURES_SETUP assets LABELS fixture)

add_test(NAME aggregate COMMAND "${CMAKE_COMMAND}" -E echo "driver placeholder")
set_tests_properties(aggregate PROPERTIES FIXTURES_REQUIRED assets LABELS "native;geometry")

add_test(NAME cleanup COMMAND "${CMAKE_COMMAND}" -E true)
set_tests_properties(cleanup PROPERTIES FIXTURES_CLEANUP assets)

add_test(NAME disabled COMMAND "${CMAKE_COMMAND}" -E false)
set_tests_properties(disabled PROPERTIES DISABLED TRUE)

add_test(NAME unavailable COMMAND "${CMAKE_BINARY_DIR}/does-not-exist")
add_test(NAME debug_only COMMAND "${CMAKE_COMMAND}" -E true CONFIGURATIONS Debug)
