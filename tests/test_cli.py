"""Tests for cli"""
import argparse
import io
import os
import shutil
import sys

import pytest
import cv2
import numpy as np
from unittest import mock
from PIL import Image

from autocrop.autocrop import Cropper
from autocrop.cli import (
    command_line_interface,
    crop_file_to_output,
    crop_stdin_to_stdout,
    main,
    output,
    output_format,
    reject,
    resolve_file_output,
    size,
    confirmation,
    chk_extension,
)

NUM_FILES = 12
SOURCE_ATIME_NS = 946684800123456000
SOURCE_MTIME_NS = 978307200654321000
EXIF_MAKE_TAG = 271


@pytest.fixture()
def integration():
    # Setup
    path_i = "tests/test"
    path_o = "tests/crop"
    path_r = "tests/reject"
    for path in [path_i, path_o, path_r]:
        shutil.rmtree(path, ignore_errors=True)
    shutil.copytree("tests/data", path_i)
    yield

    # Teardown
    for path in [path_i, path_o, path_r]:
        shutil.rmtree(path, ignore_errors=True)


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


def test_reject_preserves_source_timestamps_for_new_file(tmp_path):
    source = tmp_path / "source.jpg"
    destination = tmp_path / "reject.jpg"
    Image.new("RGB", (4, 4), "red").save(source)
    source_stat = set_source_timestamps(source)

    reject(str(source), str(destination), source_stat)

    assert_timestamps_match_source(destination)


@mock.patch("autocrop.cli.main")
def test_cli_no_args_requires_input_from_tty(mock_main, monkeypatch):
    mock_main.return_value = None
    monkeypatch.setattr("sys.stdin.isatty", lambda: True)
    sys.argv = ["", "--no-confirm"]
    with pytest.raises(SystemExit) as e:
        command_line_interface()
    assert "input image" in str(e.value)
    assert mock_main.call_count == 0


@mock.patch("autocrop.cli.crop_file_to_output")
def test_cli_file_without_output_writes_to_stdout(mock_crop):
    mock_crop.return_value = 0
    sys.argv = ["autocrop", "tests/data/obama.jpg"]
    with pytest.raises(SystemExit) as e:
        command_line_interface()
    assert e.value.code == 0
    args, _ = mock_crop.call_args
    assert args[0].endswith("tests/data/obama.jpg")
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
    sys.argv = ["autocrop", "tests/data/obama.jpg", "-w", "140", "--no-confirm"]
    assert mock_crop.call_count == 0
    with pytest.raises(SystemExit) as e:
        command_line_interface()
    assert e.value.code == 0
    assert mock_crop.call_count == 1
    args, _ = mock_crop.call_args
    assert args[4] == 140


def test_cli_invalid_input_path_errors_out():
    sys.argv = ["autocrop", "-i", "asdfasdf"]
    with pytest.raises(SystemExit) as e:
        command_line_interface()
    assert e.type == SystemExit
    assert "SystemExit" in str(e)


def test_cli_no_images_in_input_path():
    sys.argv = ["autocrop", "-i", "tests"]
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
    "from_user, response, output",
    [
        (["x", "x", "No"], False, "Please respond with 'y' or 'n'\n" * 2),
        (["y"], True, ""),
        (["n"], False, ""),
        (["x", "y"], True, "Please respond with 'y' or 'n'\n"),
    ],
)
def test_confirmation_get_from_user(from_user, response, output):
    question = "Overwrite image files?"
    input_str = "autocrop.cli.compat_input"

    with mock.patch(input_str, lambda x: from_user.pop(0)):
        with mock.patch("sys.stdout", new_callable=io.StringIO):
            assert response == confirmation(question)
            assert output == sys.stdout.getvalue()


@mock.patch("autocrop.cli.main", lambda *args: None)
@mock.patch("autocrop.cli.confirmation")
def test_directory_input_without_output_errors(mock_confirm):
    mock_confirm.return_value = False
    sys.argv = ["", "-i", "tests/data"]
    with pytest.raises(SystemExit) as e:
        assert mock_confirm.call_count == 0
        command_line_interface()
    assert mock_confirm.call_count == 0
    assert e.type == SystemExit
    assert "directory input requires --output" in str(e.value)


@mock.patch("autocrop.cli.main", lambda *args: None)
@mock.patch("autocrop.cli.confirmation")
def test_user_gets_prompted_if_output_same_as_input(mock_confirm):
    mock_confirm.return_value = False
    sys.argv = ["", "-i", "tests/data", "-o", "tests/data"]
    with pytest.raises(SystemExit) as e:
        assert mock_confirm.call_count == 0
        command_line_interface()
    assert mock_confirm.call_count == 1
    assert e.type == SystemExit


@pytest.mark.slow
def test_main_overwrites_when_same_input_and_output(integration):
    sys.argv = ["", "--no-confirm", "-i", "tests/test", "-o", "tests/test"]
    command_line_interface()
    output_files = os.listdir(sys.argv[-1])
    assert len(output_files) == NUM_FILES


# @mock.patch("autocrop.autocrop.Cropper", side_)
def test_main_overwrites_when_no_output(monkeypatch, integration):
    class MonkeyCrop:
        def __init__(self, *args):
            self.count = 0

        def crop(self, *args):
            self.count += 1
            return None

    m = MonkeyCrop()
    monkeypatch.setattr(Cropper, "crop", m.crop)
    main("tests/test", None, None, None)
    assert m.count == NUM_FILES - 1


@mock.patch("autocrop.cli.main", lambda *args: None)
@mock.patch("autocrop.cli.output_path", lambda p: p)
@mock.patch("autocrop.cli.confirmation")
def test_user_does_not_get_prompted_if_output_d_is_given(mock_confirm):
    mock_confirm.return_value = False
    sys.argv = ["", "-i", "tests/data", "-o", "tests/crop"]
    assert mock_confirm.call_count == 0
    command_line_interface()
    assert mock_confirm.call_count == 0


@mock.patch("autocrop.cli.main", lambda *args: None)
@mock.patch("autocrop.cli.confirmation")
@pytest.mark.parametrize(
    "flag",
    [
        ("--no-confirm"),
        ("--skip-prompt"),
    ],
)
def test_user_does_not_get_prompted_if_no_confirm(mock_confirm, flag):
    mock_confirm.return_value = False
    sys.argv = ["", "-i", "tests/data", "-o", "tests/crop", flag]
    assert mock_confirm.call_count == 0
    command_line_interface()
    assert mock_confirm.call_count == 0


@pytest.mark.slow
def test_noface_files_copied_over_if_output_d_specified(integration):
    sys.argv = ["", "-i", "tests/test", "-o", "tests/crop"]
    command_line_interface()
    output_files = os.listdir(sys.argv[-1])
    assert len(output_files) == NUM_FILES - 1


@pytest.mark.slow
def test_nofaces_copied_to_reject_d_if_both_reject_and_output_d(integration):
    sys.argv = [
        "",
        "-i",
        "tests/test",
        "-o",
        "tests/crop",
        "-r",
        "tests/reject",
    ]
    command_line_interface()
    output_files = os.listdir(sys.argv[-3])
    reject_files = os.listdir(sys.argv[-1])
    assert len(output_files) == NUM_FILES - 4
    assert len(reject_files) == 3


@pytest.mark.slow
@mock.patch("autocrop.cli.confirmation", lambda *args: True)
def test_image_files_overwritten_if_no_output_dir(integration):
    sys.argv = ["", "-i", "tests/test", "-o", "tests/test"]
    command_line_interface()
    # We have the same number of files
    output_files = os.listdir("tests/test")
    assert len(output_files) == NUM_FILES
    # Images with a face have been cropped
    shape = cv2.imread("tests/test/king.jpg").shape
    assert shape == (500, 500, 3)


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


@pytest.mark.slow
def test_extension_parameter(integration):
    sys.argv = [
        "",
        "-i",
        "tests/test",
        "-o",
        "tests/crop",
        "-r",
        "tests/reject",
        "-e",
        "png",
    ]
    command_line_interface()
    output_files = os.listdir("tests/crop")
    assert all(f.endswith(".png") for f in output_files)


@pytest.mark.slow
def test_no_resize_flag(integration):
    sys.argv = [
        "",
        "--no-confirm",
        "-i",
        "tests/test",
        "-o",
        "tests/crop",
        "--no-resize",
    ]
    command_line_interface()
    img = cv2.imread("tests/crop/obama.jpg")
    assert img.shape == (430, 430, 3)


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


def test_crop_stdin_to_stdout_writes_invalid_input_to_stderr(capsys):
    stdout = io.BytesIO()

    status = crop_stdin_to_stdout(stdin=io.BytesIO(b"not an image"), stdout=stdout)

    captured = capsys.readouterr()
    assert status == 1
    assert stdout.getvalue() == b""
    assert captured.out == ""
    assert "Could not read image from stdin" in captured.err
