"""Source invocation planning never substitutes for configured CTest discovery."""
import unittest

from tools.discover_unittest_cohorts import cmake_commands, registrations


class InvocationPlanTests(unittest.TestCase):
    def test_comments_quoted_parentheses_and_brackets_do_not_break_spans(self):
        source = '''
# add_blender_test(fake --python fake.py)
set(ARG "quoted ( value )" [=[bracket ) (]=])
add_blender_test(real --python ${CMAKE_CURRENT_LIST_DIR}/real.py)
'''
        commands = list(cmake_commands(source))
        self.assertEqual([item["name"] for item in commands], ["set", "add_blender_test"])
        self.assertIn("real.py", commands[1]["arguments"])

    def test_conditionals_and_loop_declarations_remain_unresolved(self):
        source = '''
if(TEST_SRC_DIR_EXISTS)
  add_blender_test(requires_fixture --python fixture.py)
else()
  foreach(name a b)
    add_blender_test(${name} --python generated.py)
  endforeach()
endif()
add_blender_test(unconditional --python literal.py)
'''
        rows = list(registrations(source))
        self.assertEqual(len(rows), 3)
        self.assertEqual(len(rows[0]["context"]), 1)
        self.assertEqual(len(rows[1]["context"]), 2)
        self.assertEqual(rows[1]["context"][0]["branch"], "else()")
        self.assertEqual(rows[2]["context"], [])

    def test_unbalanced_source_is_rejected_instead_of_shortening_plan(self):
        with self.assertRaises(ValueError):
            list(registrations("if(ENABLED)\nadd_blender_test(one --python one.py)\n"))
        with self.assertRaises(ValueError):
            list(cmake_commands("add_blender_test(one --python one.py"))


if __name__ == "__main__":
    unittest.main()
