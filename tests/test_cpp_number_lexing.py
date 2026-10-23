"""Regression coverage for C++ preprocessing-number tokens, including floating literals."""
import unittest
from tools.inventory import scan_cpp
class CppPreprocessingNumberTests(unittest.TestCase):
    def check_literal(self,literal):
        text=f'auto a={literal};\nTEST(real, Case){{}}\nauto b={literal};'
        self.assertEqual([(c['identity'],c['line']) for c in scan_cpp(text,'a.cc')],[('real.Case',2)])
    def test_decimal_floating_separators(self):self.check_literal("1'000.2'300e+0")
    def test_hexadecimal_floating_separators(self):self.check_literal("0xA'B.C'Dp+0")
    def test_leading_dot_exponent(self):self.check_literal(".1'25e-3")
    def test_user_defined_numeric_literal(self):self.check_literal("1'000_example")
    def test_exponent_separator(self):self.check_literal("1.0e+1'0")
    def test_hexadecimal_suffix(self):self.check_literal("0xF'FULL")
    def test_numeric_text_inside_strings_is_not_code(self):
        text='const char *p=".1\'25e-3 TEST(fake, Bad)"; TEST(real, Case){}'
        self.assertEqual([c['identity'] for c in scan_cpp(text,'a.cc')],['real.Case'])
if __name__=='__main__':unittest.main()
