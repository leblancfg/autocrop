"""Tests for cli"""
import argparse
import io
import os
import shutil
import sys

import pytest
import cv2
from unittest import mock

from autocrop.autocrop import Cropper
from autocrop.cli import command_line_interface, main, size, confirmation, chk_extension


@pytest.fixture()
def integration():
    # Setup
    path_i = "tests/test"
    path_o = "tests/crop"
    path_r = "tests/reject"
    shutil.copytree("tests/data", path_i)
    yield

    # Teardown
    shutil.rmtree(path_i)
    for path in [path_o, path_r]:
        try:
            shutil.rmtree(path)
        except OSError:
            pass


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


@mock.patch("autocrop.cli.input_path", lambda p: p)
@mock.patch("autocrop.cli.main")
def test_cli_no_args_means_cwd(mock_main):
    mock_main.return_value = None
    sys.argv = ["", "--no-confirm"]
    command_line_interface()
    args, _ = mock_main.call_args
    assert args == (".", None, None, None, 500, 500, 50)


@mock.patch("autocrop.cli.input_path", lambda p: p)
@mock.patch("autocrop.cli.main")
def test_cli_width_140_is_valid(mock_main):
    mock_main.return_value = None
    sys.argv = ["autocrop", "-w", "140", "--no-confirm"]
    assert mock_main.call_count == 0
    command_line_interface()
    assert mock_main.call_count == 1


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
def test_user_gets_prompted_if_no_output_is_given(mock_confirm):
    mock_confirm.return_value = False
    sys.argv = ["", "-i", "tests/data"]
    with pytest.raises(SystemExit) as e:
        assert mock_confirm.call_count == 0
        command_line_interface()
    assert mock_confirm.call_count == 1
    assert e.type == SystemExit


@mock.patch("autocrop.cli.main", lambda *args: None)
@mock.patch("autocrop.cli.confirmation")
def test_user_gets_prompted_if_output_same_as_input(mock_confirm):
    mock_confirm.return_value = False
    sys.argv = ["", "-i", "tests/data"]
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
    assert len(output_files) == 11


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
    assert m.count == 10


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
def test_user_does_not_get_prompted_if_no_confirm(mock_confirm):
    mock_confirm.return_value = False
    sys.argv = ["", "-i", "tests/data", "--no-confirm"]
    assert mock_confirm.call_count == 0
    command_line_interface()
    assert mock_confirm.call_count == 0


@pytest.mark.slow
def test_noface_files_copied_over_if_output_d_specified(integration):
    sys.argv = ["", "-i", "tests/test", "-o", "tests/crop"]
    command_line_interface()
    output_files = os.listdir(sys.argv[-1])
    assert len(output_files) == 10


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
    assert len(output_files) == 7
    assert len(reject_files) == 3


@pytest.mark.slow
@mock.patch("autocrop.cli.confirmation", lambda *args: True)
def test_image_files_overwritten_if_no_output_dir(integration):
    sys.argv = ["", "-i", "tests/test"]
    command_line_interface()
    # We have the same number of files
    output_files = os.listdir(sys.argv[-1])
    assert len(output_files) == 11
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
