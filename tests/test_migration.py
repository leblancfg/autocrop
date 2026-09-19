"""Reproduce v1 calls against v2 without touching users' image files."""

import io
import json
import re
import sys
from pathlib import Path

import cv2
import numpy as np
import pytest
from PIL import Image

from autocrop import Cropper, CropResult
from autocrop.cli import command_line_interface, crop_file_to_output, crop_stdin_to_stdout, parse_args
from autocrop.migration import FAQ_URL, REMOVED_OPTIONS, removed_cli_option


@pytest.mark.parametrize("flag", list(REMOVED_OPTIONS))
def test_removed_options_explain_migration_before_reading_input(flag, capsys):
    with pytest.raises(SystemExit) as exc:
        parse_args([flag, "nonexistent-directory-or-extension"])
    captured = capsys.readouterr()
    assert exc.value.code == 2
    assert captured.out == ""
    assert f"{flag} was removed" in captured.err
    assert FAQ_URL in captured.err
    assert "Input image does not exist" not in captured.err
    assert "Traceback" not in captured.err


@pytest.mark.parametrize(
    "arg, option",
    [
        ("-iportraits", "-i"),
        ("-epng", "-e"),
        ("-rrejected", "-r"),
        ("--input=portraits", "--input"),
        ("--extension=png", "--extension"),
    ],
)
def test_attached_legacy_values(arg, option, capsys):
    with pytest.raises(SystemExit):
        parse_args([arg])
    assert f"{option} was removed" in capsys.readouterr().err


def test_option_scanner_respects_terminator_and_argument_values():
    assert removed_cli_option(["--", "-image.jpg"]) is None
    assert removed_cli_option(["--json", "-report.json"]) is None
    assert removed_cli_option(["-o", "-input.png"]) is None


def test_dash_prefixed_source_after_terminator(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    Image.new("RGB", (2, 2)).save("-image.png")
    assert parse_args(["--", "-image.png"]).source.endswith("-image.png")


def test_directory_error_links_to_batch_instructions(tmp_path, capsys):
    with pytest.raises(SystemExit) as exc:
        parse_args([str(tmp_path)])
    assert exc.value.code == 2
    message = capsys.readouterr().err
    assert "Directory inputs" in message
    assert FAQ_URL + "#directory-mode" in message


@pytest.mark.parametrize(
    "kwargs", [{"padding": None}, {"padding": 20}, {"fix_gamma": False}, {"fix_gamma": True}, {"detector": "haar"}]
)
def test_removed_python_arguments_are_not_silently_accepted(kwargs):
    with pytest.raises(TypeError, match="Removed Cropper argument") as exc:
        Cropper(**kwargs)
    assert next(iter(kwargs)) in str(exc.value)
    assert FAQ_URL + "#python-arguments" in str(exc.value)


@pytest.mark.parametrize("args", [(None,), (None, False), (True,), (None, False, True)])
def test_old_positional_arguments_cannot_change_meaning(args):
    with pytest.raises(TypeError, match="Only width, height, and face_percent") as exc:
        Cropper(500, 500, 50, *args)
    assert "resize=False" in str(exc.value)
    assert FAQ_URL in str(exc.value)


def test_three_positional_arguments_and_keyword_options_still_work():
    cropper = Cropper(320, 240, 50, resize=False, align=True)
    assert (cropper.width, cropper.height) == (320, 240)
    assert cropper.resize is False


def test_typo_is_not_mislabeled_as_removed_argument():
    with pytest.raises(TypeError, match="unexpected keyword argument 'widht'") as exc:
        Cropper(widht=100)
    assert FAQ_URL not in str(exc.value)


def test_bare_cli_on_terminal_explains_no_directory_scan(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["autocrop"])
    monkeypatch.setattr(sys.stdin, "isatty", lambda: True)
    with pytest.raises(SystemExit) as exc:
        command_line_interface()
    assert "current directory is no longer scanned" in str(exc.value)
    assert FAQ_URL in str(exc.value)
    assert capsys.readouterr().out == ""


def test_empty_pipe_explains_version_flag(capsys):
    output = io.BytesIO()
    assert crop_stdin_to_stdout(stdin=io.BytesIO(), stdout=output) == 1
    message = capsys.readouterr().err
    assert "-V or --version" in message
    assert "-v is verbose" in message
    assert FAQ_URL in message
    assert output.getvalue() == b""


def test_migration_error_is_still_json(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["autocrop", "-i", "portraits", "--json", "-"])
    with pytest.raises(SystemExit) as exc:
        command_line_interface()
    assert exc.value.code == 2
    metadata = json.loads(capsys.readouterr().err)
    assert metadata["error"] == "cli_error"
    assert "-i was removed" in metadata["message"]
    assert FAQ_URL in metadata["message"]


def test_stdin_output_option_is_rejected_before_writing(tmp_path, monkeypatch, capsys):
    destination = tmp_path / "crop.jpg"
    monkeypatch.setattr(sys, "argv", ["autocrop", "-", "-o", str(destination), "--json", "-"])
    with pytest.raises(SystemExit) as exc:
        command_line_interface()
    assert exc.value.code == 2
    assert not destination.exists()
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "Redirect stdout" in json.loads(captured.err)["message"]


def test_old_opencv_gets_actionable_error(monkeypatch, capsys):
    monkeypatch.delattr(cv2, "FaceDetectorYN_create")
    with pytest.raises(RuntimeError, match="opencv-python-headless>=4.8"):
        Cropper().crop("tests/data/obama.jpg")
    assert crop_file_to_output("tests/data/obama.jpg", stdout=io.BytesIO(), json_output="-") == 1
    metadata = json.loads(capsys.readouterr().err)
    assert metadata["error"] == "process_error"
    assert FAQ_URL + "#dependencies" in metadata["message"]


def test_missing_model_explains_reinstall():
    with pytest.raises(FileNotFoundError, match="reinstall autocrop") as exc:
        Cropper(yunet_model_path="missing.onnx").crop("tests/data/obama.jpg")
    assert FAQ_URL in str(exc.value)


def test_faq_links_are_real_sections():
    content = Path("docs/faq.md").read_text()
    sections = set(re.findall(r"\{#([a-z-]+)\}", content))
    assert set(REMOVED_OPTIONS.values()) <= sections
    assert {"python-arguments", "dependencies", "no-input", "stdout", "rollback"} <= sections
    assert "faq/" in Path("README.md").read_text()
    assert "'/faq/'" in Path("docs/_layouts/default.html").read_text()


def test_v1_python_caller_migrates_to_result_image():
    result = Cropper(width=100, height=100, face_percent=50).crop("tests/data/obama.jpg")
    assert isinstance(result, CropResult)
    assert isinstance(result.image, np.ndarray)
    assert result.image.shape == (100, 100, 3)
