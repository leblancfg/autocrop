"""Regression tests for per-call result records and machine-readable output."""

import io
import json
import os
import sys
from dataclasses import asdict, is_dataclass

import numpy as np
import pytest
from PIL import Image

from autocrop import CropDiagnostics, Cropper, CropResult, reporting
from autocrop.cli import command_line_interface, crop_file_to_output, crop_stdin_to_stdout


@pytest.mark.parametrize("source", ["tests/data/obama.jpg", "tests/data/noise.png"])
def test_crop_always_returns_typed_result(source):
    cropper = Cropper()
    result = cropper.crop(source)
    assert isinstance(result, CropResult)
    assert isinstance(result.diagnostics, CropDiagnostics)
    assert is_dataclass(result.diagnostics)
    if result.image is None:
        assert result.diagnostics.error == "no_face_detected"
    else:
        assert isinstance(result.image, np.ndarray)
        assert 0 <= result.diagnostics.faces[0].score <= 1
    json.dumps(asdict(result.diagnostics), allow_nan=False)
    assert not hasattr(cropper, "crop_with_diagnostics")
    assert not hasattr(cropper, "diagnostics")


def test_results_are_independent_across_calls_and_instances():
    cropper = Cropper()
    first = cropper.crop("tests/data/obama.jpg")
    snapshot = asdict(first.diagnostics)
    second = cropper.crop("tests/data/noise.png")
    with pytest.raises(FileNotFoundError):
        cropper.crop("missing.jpg")
    third = cropper.crop("tests/data/obama.jpg")
    assert asdict(first.diagnostics) == snapshot
    assert second.diagnostics.error == "no_face_detected"
    assert third.diagnostics.error is None
    assert first.diagnostics is not third.diagnostics
    assert Cropper().crop("tests/data/obama.jpg").diagnostics is not first.diagnostics
    assert first != third  # No ambiguous ndarray comparison from generated __eq__.


def test_result_does_not_pretend_to_be_an_array_or_tuple():
    result = Cropper().crop("tests/data/obama.jpg")
    with pytest.raises(TypeError):
        tuple(result)
    assert not hasattr(result, "__array__")


def test_invalid_detector_configuration_still_raises():
    with pytest.raises(FileNotFoundError):
        Cropper(yunet_model_path="missing-model.onnx").crop("tests/data/obama.jpg")


def test_diagnostics_flag_is_not_part_of_the_api():
    with pytest.raises(TypeError):
        Cropper().crop("tests/data/obama.jpg", diagnostics=True)
    with pytest.raises(TypeError):
        Cropper().crop("tests/data/obama.jpg", True)


@pytest.mark.parametrize("exists", [False, True])
def test_unreadable_file_still_raises(tmp_path, exists):
    path = tmp_path / "invalid.jpg"
    if exists:
        path.write_bytes(b"not an image")
    with pytest.raises(OSError):
        Cropper().crop(str(path))


def test_model_path_is_json_serializable():
    from pathlib import Path

    cropper = Cropper(yunet_model_path=Path("autocrop/face_detection_yunet_2023mar.onnx"))
    result = cropper.crop("tests/data/obama.jpg")
    assert isinstance(result.diagnostics.detector.settings["model_path"], str)
    json.dumps(asdict(result.diagnostics))


@pytest.mark.parametrize("verbose", [False, True])
@pytest.mark.parametrize("source", ["tests/data/obama.jpg", "tests/data/noise.png", "missing.jpg"])
def test_json_stderr_is_one_document(source, verbose, capsys):
    stdout = io.BytesIO()
    status = crop_file_to_output(source, stdout=stdout, json_output="-", verbose=verbose)
    captured = capsys.readouterr()
    metadata = json.loads(captured.err)
    assert captured.out == ""
    assert "timings" in metadata
    assert status == int(metadata["error"] is not None)
    if status:
        assert stdout.getvalue() == b""
    else:
        with Image.open(io.BytesIO(stdout.getvalue())) as image:
            assert image.size == (500, 500)


@pytest.mark.parametrize("data", [b"", b"invalid"])
def test_stdin_errors_are_json(data, capsys):
    stdout = io.BytesIO()
    assert crop_stdin_to_stdout(stdin=io.BytesIO(data), stdout=stdout, json_output="-", verbose=True) == 1
    assert json.loads(capsys.readouterr().err)["error"] == "read_error"
    assert stdout.getvalue() == b""


@pytest.mark.parametrize(
    "args",
    [
        ["missing.jpg", "--json", "-"],
        ["--unknown", "--json=-"],
        ["tests/data/obama.jpg", "-o", "crop.bad", "--json", "-"],
    ],
)
def test_cli_argument_errors_are_json(args, monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["autocrop", *args])
    with pytest.raises(SystemExit) as exc:
        command_line_interface()
    assert exc.value.code == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert json.loads(captured.err)["error"] == "cli_error"


@pytest.mark.parametrize("target", ["input", "output"])
@pytest.mark.parametrize("alias", ["same", "relative", "symlink", "hardlink"])
def test_json_cannot_overwrite_images(tmp_path, target, alias, monkeypatch, capsys):
    source = tmp_path / "source.png"
    destination = tmp_path / "cropped.png"
    Image.new("RGB", (10, 10), "red").save(source)
    destination.write_bytes(b"existing output")
    target_path = source if target == "input" else destination
    json_path = target_path
    if alias == "relative":
        monkeypatch.chdir(tmp_path)
        json_path = target_path.name
    elif alias in ("symlink", "hardlink"):
        json_path = tmp_path / "alias.json"
        try:
            if alias == "symlink":
                json_path.symlink_to(target_path)
            else:
                os.link(target_path, json_path)
        except OSError:
            pytest.skip("filesystem does not support this link type")
    original, old_output = source.read_bytes(), destination.read_bytes()
    stdout = io.BytesIO()
    assert crop_file_to_output(source, destination, stdout=stdout, json_output=json_path) == 2
    assert source.read_bytes() == original
    assert destination.read_bytes() == old_output
    assert stdout.getvalue() == b""
    assert "must not overwrite" in capsys.readouterr().err


@pytest.mark.parametrize("mode", ["stdin", "stdout"])
def test_json_cannot_overwrite_redirected_stream(tmp_path, mode, capsys):
    path = tmp_path / "redirected.png"
    Image.new("RGB", (10, 10), "red").save(path)
    original = path.read_bytes()
    with path.open("r+b") as stream:
        if mode == "stdin":
            status = crop_stdin_to_stdout(stdin=stream, stdout=io.BytesIO(), json_output=path)
        else:
            status = crop_file_to_output("tests/data/obama.jpg", stdout=stream, json_output=path)
    assert status == 2
    assert path.read_bytes() == original
    assert "redirected image stream" in capsys.readouterr().err


def test_json_write_failure_is_nonzero_without_traceback(tmp_path, capsys):
    destination = tmp_path / "directory"
    destination.mkdir()
    status = crop_file_to_output("tests/data/obama.jpg", stdout=io.BytesIO(), json_output=destination)
    assert status == 1
    message = capsys.readouterr().err
    assert "Could not write JSON diagnostics" in message
    assert "Traceback" not in message
    assert list(tmp_path.iterdir()) == [destination]


def test_failed_json_replace_preserves_old_file(tmp_path, monkeypatch):
    path = tmp_path / "diagnostics.json"
    path.write_text("old diagnostics")

    def fail(*args):
        raise OSError("disk full")

    monkeypatch.setattr(os, "replace", fail)
    with pytest.raises(OSError, match="disk full"):
        reporting.write({"error": None}, path)
    assert path.read_text() == "old diagnostics"
    assert list(tmp_path.iterdir()) == [path]


def test_image_write_error_is_json(monkeypatch, capsys):
    def fail(*args):
        raise PermissionError("read-only destination")

    monkeypatch.setattr("autocrop.cli.output_bytes", fail)
    assert crop_file_to_output("tests/data/obama.jpg", stdout=io.BytesIO(), json_output="-") == 1
    result = json.loads(capsys.readouterr().err)
    assert result["error"] == "write_error"
    assert "read-only destination" in result["message"]
