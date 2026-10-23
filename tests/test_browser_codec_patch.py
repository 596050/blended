"""Include the real codec patch regressions in the ordinary infrastructure gate."""
import importlib.util
from pathlib import Path


def load_tests(loader, standard_tests, pattern):
    source = Path(__file__).resolve().parents[1] / "patches/browser-codecs/test_patch.py"
    specification = importlib.util.spec_from_file_location("browser_codec_patch_regressions", source)
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return loader.loadTestsFromModule(module)
