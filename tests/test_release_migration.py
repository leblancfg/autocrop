"""Release-facing migration errors must lead to real, documented replacements."""

import ast
import copy
import importlib
import pickle
import re
from pathlib import Path

import pytest
from PIL import Image

from autocrop import Cropper, CropResult, __version__
from autocrop.migration import FAQ_URL, REMOVED_CONSTANTS

REMOVED_HELPERS = [
    ("autocrop.autocrop", "gamma"),
    ("autocrop.autocrop", "check_underexposed"),
    ("autocrop.autocrop", "COMBINED_FILETYPES"),
    ("autocrop.cli", "main"),
    ("autocrop.cli", "reject"),
    ("autocrop.cli", "output_path"),
    ("autocrop.cli", "compat_input"),
    ("autocrop.cli", "confirmation"),
    ("autocrop.cli", "chk_extension"),
    ("autocrop.cli", "COMBINED_FILETYPES"),
]


def assert_faq_link(error):
    message = str(error)
    assert "autocrop 2.0.0:" in message
    match = re.search(re.escape(FAQ_URL) + r"#([a-z-]+)", message)
    assert match is not None, message
    assert f"{{#{match[1]}}}" in Path("docs/faq.md").read_text()


@pytest.mark.parametrize("module,name", REMOVED_HELPERS)
def test_removed_helper_imports_retain_migration_message(module, name):
    # A real from-import matters: Python discards AttributeError from module __getattr__.
    with pytest.raises(ImportError) as exc:
        exec(f"from {module} import {name}", {})
    assert f"{module}.{name} was removed" in str(exc.value)
    assert_faq_link(exc.value)


@pytest.mark.parametrize("name", REMOVED_CONSTANTS)
@pytest.mark.parametrize("module", ["autocrop.constants", "autocrop.autocrop", "autocrop.cli"])
def test_removed_constant_imports_retain_migration_message(module, name):
    with pytest.raises(ImportError) as exc:
        exec(f"from {module} import {name}", {})
    assert name in str(exc.value)
    assert_faq_link(exc.value)


@pytest.mark.parametrize("module", ["autocrop.constants", "autocrop.autocrop", "autocrop.cli"])
def test_unknown_module_attribute_is_not_mislabeled_as_a_removed_api(module):
    with pytest.raises(AttributeError) as exc:
        getattr(importlib.import_module(module), "not_an_autocrop_attribute")
    assert FAQ_URL not in str(exc.value)


@pytest.mark.parametrize("name", ["crop_with_diagnostics", "diagnostics", "gamma", "casc_path"])
def test_removed_cropper_attributes_explain_replacement(name):
    cropper = Cropper()
    with pytest.raises(AttributeError) as exc:
        getattr(cropper, name)
    assert name in str(exc.value)
    assert_faq_link(exc.value)
    assert not hasattr(cropper, name)


@pytest.mark.parametrize("name", ["gamma", "casc_path", "diagnostics"])
def test_removed_cropper_assignments_cannot_silently_do_nothing(name):
    cropper = Cropper()
    with pytest.raises(AttributeError) as exc:
        setattr(cropper, name, True)
    assert name not in vars(cropper)
    assert_faq_link(exc.value)


@pytest.mark.parametrize(
    "positional,keywords", [((), {"diagnostics": True}), ((), {"diagnostics": False}), ((True,), {})]
)
def test_draft_crop_arguments_fail_before_reading_source(positional, keywords, monkeypatch):
    module = importlib.import_module("autocrop.autocrop")

    def must_not_read(*args):
        pytest.fail("Legacy arguments must be rejected before opening the source")

    monkeypatch.setattr(module, "open_file", must_not_read)
    with pytest.raises(TypeError) as exc:
        Cropper().crop("missing.jpg", *positional, **keywords)
    assert "result.image and result.diagnostics" in str(exc.value)
    assert_faq_link(exc.value)


def test_crop_keyword_typo_is_not_mislabeled_as_migration():
    with pytest.raises(TypeError, match="unexpected keyword argument 'diagnostic'") as exc:
        Cropper().crop("missing.jpg", diagnostic=True)
    assert FAQ_URL not in str(exc.value)


@pytest.fixture(params=["tests/data/obama.jpg", "tests/data/noise.png"])
def result(request):
    return Cropper().crop(request.param)


@pytest.mark.parametrize("operation", [bool, len, tuple, lambda result: result[0], Image.fromarray])
def test_using_record_as_image_or_tuple_explains_image_field(result, operation):
    with pytest.raises((TypeError, AttributeError)) as exc:
        operation(result)
    assert "result.image" in str(exc.value)
    assert_faq_link(exc.value)


@pytest.mark.parametrize("attribute", ["shape", "dtype", "ndim", "size", "copy", "astype", "__array_interface__"])
def test_array_attribute_access_explains_image_field(result, attribute):
    with pytest.raises(AttributeError) as exc:
        getattr(result, attribute)
    assert "result.image" in str(exc.value)
    assert_faq_link(exc.value)


def test_result_remains_a_plain_record_with_no_array_protocol(result):
    assert isinstance(result, CropResult)
    assert not hasattr(result, "__array__")
    assert not hasattr(result, "__array_interface__")
    # Identity checks cannot be intercepted; callers must migrate them explicitly.
    assert result is not None
    assert (result.image is None) == (result.diagnostics.error is not None)
    restored = pickle.loads(pickle.dumps(result))
    copied = copy.deepcopy(result)
    assert restored.diagnostics == result.diagnostics
    assert copied.diagnostics == result.diagnostics


def test_runtime_migration_links_have_real_faq_sections():
    sections = set(re.findall(r"\{#([a-z-]+)\}", Path("docs/faq.md").read_text()))
    for path in Path("autocrop").glob("*.py"):
        for node in ast.walk(ast.parse(path.read_text())):
            if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Name):
                continue
            if node.func.id == "migration_message" and len(node.args) == 2:
                section = node.args[1]
                if isinstance(section, ast.Constant):
                    assert section.value in sections, (path, section.value)
    assert {section for _, section in REMOVED_CONSTANTS.values()} <= sections


def test_release_version_and_documentation_agree():
    assert __version__ == "2.0.0"
    changelog = Path("docs/changelog.md").read_text()
    match = re.search(r"^## 2\.0\.0 - (\d{4}-\d{2}-\d{2})$", changelog, re.MULTILINE)
    assert match is not None
    for name in ("index", "quickstart", "api", "cli", "faq"):
        content = Path(f"docs/{name}.md").read_text()
        assert "2.0.0" in content
        assert match[1] in content
        assert "Unreleased" not in content
    assert "Pending 2.0.0 review stack" not in Path("CONTRIBUTING.md").read_text()
