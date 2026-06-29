"""Tests for cli"""
import argparse
import io
import os
import re
import sys

import pytest
import numpy as np
from unittest import mock
from PIL import Image

from autocrop.autocrop import Cropper
from autocrop.cli import (
    command_line_interface,
    crop_file_to_output,
    crop_stdin_to_stdout,
    output,
    output_format,
    resolve_file_output,
    size,
    chk_extension,
)

SOURCE_ATIME_NS = 946684800123456000
SOURCE_MTIME_NS = 978307200654321000
EXIF_MAKE_TAG = 271


def verbose_timing(captured_err, key):
    match = re.search(rf"{key}=([0-9]+\.[0-9]+)s", captured_err)
    assert match is not None
    return float(match.group(1))


def test_size_140_is_valid():
    assert size(140) == 140


def test_size_0_not_valid():
    with pytest.raises(Exception) as e:
        size(0)
    assert "Invalid pixel" in str(e)


def test_size_million_not_valid():
    with pytest.raises(Exception) as e:
        size(1e6)
    assert "Invalid pixel" in str(e)


def test_size_asdf_gives_ValueError():
    with pytest.raises(Exception) as e:
        size("asdf")
    assert "Error" in str(e)


def test_size_minus_14_not_valid():
    with pytest.raises(Exception) as e:
        size(-14)
        print(e)
    assert "Invalid pixel" in str(e)


def set_source_timestamps(path):
    os.utime(path, ns=(SOURCE_ATIME_NS, SOURCE_MTIME_NS))
    return os.stat(path)


def assert_timestamps_match_source(path):
    metadata = os.stat(path)
    assert metadata.st_atime_ns == SOURCE_ATIME_NS
    assert metadata.st_mtime_ns == SOURCE_MTIME_NS


def exif_image(path):
    exif = Image.Exif()
    exif[EXIF_MAKE_TAG] = "autocrop-test-camera"
    Image.new("RGB", (4, 4), "red").save(path, exif=exif)


def assert_exif_matches_source(source, destination):
    with Image.open(source) as source_image, Image.open(destination) as result_image:
        assert result_image.getexif()[EXIF_MAKE_TAG] == source_image.getexif()[
            EXIF_MAKE_TAG
        ]


def test_output_preserves_source_timestamps_for_new_file(tmp_path):
    source = tmp_path / "source.jpg"
    destination = tmp_path / "destination.jpg"
    Image.new("RGB", (4, 4), "red").save(source)
    source_stat = set_source_timestamps(source)

    image = np.full((2, 2, 3), 255, dtype=np.uint8)
    output(str(source), str(destination), image, source_stat)

    assert_timestamps_match_source(destination)
    with Image.open(destination) as result:
        assert result.size == (2, 2)


def test_output_preserves_exif_for_new_file(tmp_path):
    source = tmp_path / "source.jpg"
    destination = tmp_path / "destination.jpg"
    exif_image(source)

    image = np.full((2, 2, 3), 255, dtype=np.uint8)
    output(str(source), str(destination), image)

    assert_exif_matches_source(source, destination)
    with Image.open(destination) as result:
        assert result.size == (2, 2)


def test_output_preserves_source_timestamps_when_overwriting(tmp_path):
    source = tmp_path / "source.jpg"
    Image.new("RGB", (4, 4), "red").save(source)
    source_stat = set_source_timestamps(source)

    image = np.full((2, 2, 3), 255, dtype=np.uint8)
    output(str(source), str(source), image, source_stat)

    assert_timestamps_match_source(source)
    with Image.open(source) as result:
        assert result.size == (2, 2)


def test_output_preserves_exif_when_overwriting(tmp_path):
    source = tmp_path / "source.jpg"
    exif_image(source)

    image = np.full((2, 2, 3), 255, dtype=np.uint8)
    output(str(source), str(source), image)

    with Image.open(source) as result:
        assert result.getexif()[EXIF_MAKE_TAG] == "autocrop-test-camera"
        assert result.size == (2, 2)


@mock.patch("autocrop.cli.crop_file_to_output")
def test_cli_no_args_requires_input_from_tty(mock_crop, monkeypatch):
    mock_crop.return_value = 0
    monkeypatch.setattr("sys.stdin.isatty", lambda: True)
    sys.argv = ["autocrop"]
    with pytest.raises(SystemExit) as e:
        command_line_interface()
    assert "input image" in str(e.value)
    assert mock_crop.call_count == 0


@mock.patch("autocrop.cli.crop_file_to_output")
def test_cli_file_without_output_writes_to_stdout(mock_crop):
    mock_crop.return_value = 0
    sys.argv = ["autocrop", "tests/data/obama.jpg"]
    with pytest.raises(SystemExit) as e:
        command_line_interface()
    assert e.value.code == 0
    args, _ = mock_crop.call_args
    assert args[0].replace("\\", "/").endswith("tests/data/obama.jpg")
    assert args[1] is None


@mock.patch("autocrop.cli.crop_stdin_to_stdout")
def test_cli_dash_reads_stdin_and_writes_stdout(mock_crop):
    mock_crop.return_value = 0
    sys.argv = ["autocrop", "-"]
    with pytest.raises(SystemExit) as e:
        command_line_interface()
    assert e.value.code == 0
    assert mock_crop.call_count == 1


@mock.patch("autocrop.cli.crop_stdin_to_stdout")
def test_cli_no_args_reads_stdin_when_input_is_piped(mock_crop, monkeypatch):
    mock_crop.return_value = 0
    monkeypatch.setattr("sys.stdin.isatty", lambda: False)
    sys.argv = ["autocrop"]
    with pytest.raises(SystemExit) as e:
        command_line_interface()
    assert e.value.code == 0
    assert mock_crop.call_count == 1


@mock.patch("autocrop.cli.crop_file_to_output")
def test_cli_width_140_is_valid(mock_crop):
    mock_crop.return_value = 0
    sys.argv = ["autocrop", "tests/data/obama.jpg", "-w", "140"]
    assert mock_crop.call_count == 0
    with pytest.raises(SystemExit) as e:
        command_line_interface()
    assert e.value.code == 0
    assert mock_crop.call_count == 1
    args, _ = mock_crop.call_args
    assert args[4] == 140


def test_cli_short_version_exits(capsys):
    sys.argv = ["autocrop", "-V"]
    with pytest.raises(SystemExit) as e:
        command_line_interface()
    captured = capsys.readouterr()
    assert e.value.code == 0
    assert "autocrop version" in captured.out
    assert captured.err == ""


@pytest.mark.parametrize("flag", ["--verbose", "-v"])
@mock.patch("autocrop.cli.crop_file_to_output")
def test_cli_verbose_is_passed_to_file_mode(mock_crop, flag):
    mock_crop.return_value = 0
    sys.argv = ["autocrop", "tests/data/obama.jpg", flag]
    with pytest.raises(SystemExit) as e:
        command_line_interface()
    assert e.value.code == 0
    _, kwargs = mock_crop.call_args
    assert kwargs["verbose"] is True


@pytest.mark.parametrize("flag", ["--verbose", "-v"])
@mock.patch("autocrop.cli.crop_stdin_to_stdout")
def test_cli_verbose_is_passed_to_stdin_mode(mock_crop, flag):
    mock_crop.return_value = 0
    sys.argv = ["autocrop", "-", flag]
    with pytest.raises(SystemExit) as e:
        command_line_interface()
    assert e.value.code == 0
    _, kwargs = mock_crop.call_args
    assert kwargs["verbose"] is True


def test_cli_invalid_input_path_errors_out():
    sys.argv = ["autocrop", "asdfasdf"]
    with pytest.raises(SystemExit) as e:
        command_line_interface()
    assert e.type == SystemExit
    assert "SystemExit" in str(e)


def test_cli_directory_input_errors_out():
    sys.argv = ["autocrop", "tests"]
    with pytest.raises(SystemExit) as e:
        command_line_interface()
    assert e.type == SystemExit
    assert "SystemExit" in str(e)


def test_cli_width_0_not_valid():
    sys.argv = ["autocrop", "-w", "0"]
    with pytest.raises(SystemExit) as e:
        command_line_interface()
    assert e.type == SystemExit
    assert "SystemExit" in str(e)


def test_cli_width_minus_14_not_valid():
    sys.argv = ["autocrop", "-w", "-14"]
    with pytest.raises(SystemExit) as e:
        command_line_interface()
    assert e.type == SystemExit
    assert "SystemExit" in str(e)


@pytest.mark.parametrize(
    "extension, error_expected, expected",
    [
        (".png", False, "png"),
        ("png", False, "png"),
        ("PNG", False, "png"),
        ("fake_ext", True, None),
        (".fake_ext", True, None),
        ("", True, None),
    ],
)
def test_check_extension(extension, error_expected, expected):
    if error_expected:
        pytest.raises(argparse.ArgumentTypeError, chk_extension, extension)
    else:
        assert chk_extension(extension) == expected


def test_output_format_uses_pillow_format_name_for_extensions():
    assert output_format("PNG", "jpg") == "JPEG"


def test_resolve_file_output_keeps_output_directory_behavior(tmp_path):
    output_filename = resolve_file_output("tests/data/obama.jpg", str(tmp_path), None)
    assert output_filename == os.path.join(str(tmp_path), "obama.jpg")


def test_crop_file_to_output_writes_explicit_file(monkeypatch, tmp_path):
    image = Image.open("tests/data/obama.jpg")
    cropped = image.resize((32, 32))
    destination = tmp_path / "cropped.jpg"
    monkeypatch.setattr(Cropper, "crop", lambda *args: np.array(cropped))

    status = crop_file_to_output(
        "tests/data/obama.jpg",
        output_filename=str(destination),
        fheight=32,
        fwidth=32,
    )

    with Image.open(destination) as result:
        assert status == 0
        assert result.size == (32, 32)


def test_crop_file_to_output_writes_cropped_bytes_to_stdout(monkeypatch, capsys):
    image = Image.open("tests/data/obama.jpg")
    cropped = image.resize((32, 32))
    stdout = io.BytesIO()
    monkeypatch.setattr(Cropper, "crop", lambda *args: np.array(cropped))

    status = crop_file_to_output(
        "tests/data/obama.jpg",
        stdout=stdout,
        fheight=32,
        fwidth=32,
    )

    stdout.seek(0)
    with Image.open(stdout) as result:
        assert status == 0
        assert result.size == (32, 32)
        assert result.format == "JPEG"
    assert capsys.readouterr().err == ""


def test_crop_file_to_output_verbose_writes_timings_to_stderr(monkeypatch, capsys):
    image = Image.open("tests/data/obama.jpg")
    cropped = image.resize((32, 32))
    stdout = io.BytesIO()
    monkeypatch.setattr(Cropper, "crop", lambda *args: np.array(cropped))

    status = crop_file_to_output(
        "tests/data/obama.jpg",
        stdout=stdout,
        fheight=32,
        fwidth=32,
        verbose=True,
    )

    captured = capsys.readouterr()
    assert status == 0
    assert captured.out == ""
    assert "Input: tests/data/obama.jpg" in captured.err
    assert "Output: stdout" in captured.err
    assert "Format: JPEG" in captured.err
    assert "Timings:" in captured.err
    for key in ["total=", "imports=", "read=", "process=", "write="]:
        assert key in captured.err
    assert verbose_timing(captured.err, "total") >= verbose_timing(
        captured.err, "imports"
    )


def test_crop_file_to_output_writes_failures_to_stderr(monkeypatch, capsys):
    stdout = io.BytesIO()
    monkeypatch.setattr(Cropper, "crop", lambda *args: None)

    status = crop_file_to_output("tests/data/noise.png", stdout=stdout)

    captured = capsys.readouterr()
    assert status == 1
    assert stdout.getvalue() == b""
    assert captured.out == ""
    assert "No face detected: tests/data/noise.png" in captured.err


def test_crop_stdin_to_stdout_infers_image_type(monkeypatch):
    source = io.BytesIO()
    Image.new("RGB", (40, 40), "white").save(source, format="PNG")
    source.seek(0)
    stdout = io.BytesIO()
    monkeypatch.setattr(
        Cropper, "crop", lambda *args: np.array(Image.new("RGB", (20, 20), "white"))
    )

    status = crop_stdin_to_stdout(stdin=source, stdout=stdout)

    stdout.seek(0)
    with Image.open(stdout) as result:
        assert status == 0
        assert result.size == (20, 20)
        assert result.format == "PNG"


def test_crop_stdin_to_stdout_verbose_writes_timings_to_stderr(monkeypatch, capsys):
    source = io.BytesIO()
    Image.new("RGB", (40, 40), "white").save(source, format="PNG")
    source.seek(0)
    stdout = io.BytesIO()
    monkeypatch.setattr(
        Cropper, "crop", lambda *args: np.array(Image.new("RGB", (20, 20), "white"))
    )

    status = crop_stdin_to_stdout(stdin=source, stdout=stdout, verbose=True)

    captured = capsys.readouterr()
    assert status == 0
    assert captured.out == ""
    assert "Input: stdin" in captured.err
    assert "Output: stdout" in captured.err
    assert "Format: PNG" in captured.err
    assert "Timings:" in captured.err
    for key in ["total=", "imports=", "read=", "process=", "write="]:
        assert key in captured.err
    assert verbose_timing(captured.err, "total") >= verbose_timing(
        captured.err, "imports"
    )


def test_crop_stdin_to_stdout_writes_invalid_input_to_stderr(capsys):
    stdout = io.BytesIO()

    status = crop_stdin_to_stdout(stdin=io.BytesIO(b"not an image"), stdout=stdout)

    captured = capsys.readouterr()
    assert status == 1
    assert stdout.getvalue() == b""
    assert captured.out == ""
    assert "Could not read image from stdin" in captured.err
