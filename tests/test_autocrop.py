# -*- coding: utf-8 -*-

"""Tests for autocrop"""

import io
import os
import sys

try:
    import mock
except ImportError:
    from unittest import mock
import pytest
import cv2
import numpy as np

from autocrop.autocrop import (
        gamma,
        crop,
        cli,
        size,
        confirmation,
)

PY3 = (sys.version_info[0] >= 3)


def test_gamma_brightens_image():
    """This function is so tightly coupled to cv2 it's probably useless.
    Still might flag cv2 or numpy boo-boos."""
    matrix = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
    expected = np.uint8([[15, 22, 27], [31, 35, 39], [42, 45, 47]])
    np.testing.assert_array_equal(gamma(img=matrix, correction=0.5), expected)


def test_crop_noise_returns_none():
    loc = 'tests/data/noise.png'
    noise = cv2.imread(loc)
    assert crop(noise) is None


def test_obama_has_a_face():
    loc = 'tests/data/obama.jpg'
    obama = cv2.imread(loc)
    assert len(crop(obama, 500, 500)) == 500


def test_size_140_is_valid():
    assert size(140) == 140


def test_size_0_not_valid():
    with pytest.raises(Exception) as e:
        size(0)
        assert 'Invalid pixel' in str(e)


def test_size_million_not_valid():
    with pytest.raises(Exception) as e:
        size(1e6)
        assert 'Invalid pixel' in str(e)


def test_size_asdf_not_valid():
    with pytest.raises(Exception) as e:
        size('asdf')
        assert 'Invalid pixel' in str(e)


def test_size_minus_14_not_valid():
    with pytest.raises(Exception) as e:
        size(-14)
        assert 'Invalid pixel' in str(e)


def test_cli_width_0_not_valid():
    sys.argv = ['autocrop', '-o', './crop', '-w', '0']
    with pytest.raises(SystemExit) as e:
        cli()
        assert e.type == SystemExit
        assert 'Invalid pixel' in str(e)
    os.rmdir('./crop')


def test_cli_width_minus_14_not_valid():
    sys.argv = ['autocrop', '-o', './crop', '-w', '-14']
    with pytest.raises(SystemExit) as e:
        cli()
        assert e.type == SystemExit
        assert 'Invalid pixel' in str(e)
    os.rmdir('./crop')


@pytest.mark.parametrize("from_user, response, output", [
    (['x', 'x', 'No'], False, "Please respond with 'y' or 'n'\n" * 2),
    (['y'], True, ''),
    (['n'], False, ''),
    (['x', 'y'], True, "Please respond with 'y' or 'n'\n"),
])
def test_confirmation_get_from_user(from_user, response, output):
    question = "Overwrite image files?"
    input_f = 'autocrop.autocrop.compat_input'

    with mock.patch(input_f, lambda x: from_user.pop(0)):
        sio = io.StringIO if PY3 else io.BytesIO
        with mock.patch('sys.stdout', new_callable=sio):
            assert response == confirmation(question)
            assert output == sys.stdout.getvalue()


@pytest.mark.parametrize("argv, called, response", [
    (['-o', 'output'], False, True),
    ([], True, False),
    ([], True, True),
    (['-i', 'crop', '-o', 'crop'], True, False),
])
def test_user_gets_prompted_if_i_equals_o(argv, called, response):
    global confirmation
    original_confirm = confirmation
    confirmation = mock.Mock(return_value=response)
    with mock.patch('sys.argv', [''] + argv):
        if called and not response:
            with pytest.raises(SystemExit):
                cli()
        else:
            cli()

        assert confirmation.called == called
    confirmation = original_confirm


# def test_cli_no_input_and_output_prompts_overwrite(capsys, monkeypatch):
#     monkeypatch.setattr('autocrop.confirmation', lambda x: '')
#     question = "Overwrite images files in "
#     sys.argv = ['autocrop']
#     cli()
#     out, err = capsys.readouterr()
#     assert out == question
#
#
# def test_cli_no_path_args_overwrites_images_in_pwd():
#     # TODO: Copy images to data/copy
#     sys.argv = ['autocrop', '-w', '400']
#     input_loc = 'tests/data/copy'
#     output_loc = 'tests/data/crop'
#
#     cli()
#     assert len(glob(output_loc)) == 7
#
#
# def test_cli_default_args_in_parent_dir():
#     # TODO: Copy images to data/copy
#     sys.argv = ['autocrop', '-i', input_loc, '-p', output_loc]
#     input_loc = 'tests/data/copy'
#     output_loc = 'tests/data/crop'
#
#     cli()
#     assert len(glob(output_loc)) == 7
#
#
# def test_uppercase_filetypes():
#     assert main() == main()
