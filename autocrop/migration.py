"""Actionable messages for calls that used the v1 interface."""

from typing import NoReturn

FAQ_URL = "https://leblancfg.com/autocrop/faq/"

# These constants were also imported into the v1 processing and CLI modules.
REMOVED_CONSTANTS = {
    "FIXEXP": ("Apply brightness correction after cropping.", "python-helpers"),
    "GAMMA": ("Apply brightness correction after cropping.", "python-helpers"),
    "GAMMA_THRES": ("Apply brightness correction after cropping.", "python-helpers"),
    "MINFACE": ("Haar tuning was removed; YuNet is the built-in detector.", "different-results"),
    "INCREMENT": ("Haar tuning was removed; YuNet is the built-in detector.", "different-results"),
    "FACE_RATIO": ("Use Cropper(face_percent=...) to control crop margins.", "python-arguments"),
    "CASCFILE": ("The Haar model was removed; YuNet ships with autocrop.", "different-results"),
    "QUESTION_OVERWRITE": ("Implement overwrite prompts in your own application.", "python-helpers"),
    "CV2_FILETYPES": ("Use autocrop.constants.INPUT_FILETYPES; Pillow now decodes path inputs.", "python-helpers"),
    "PILLOW_FILETYPES": ("Use autocrop.constants.INPUT_FILETYPES; Pillow now decodes path inputs.", "python-helpers"),
}


def migration_message(message: str, section: str) -> str:
    return f"autocrop 2.0.0: {message} See {FAQ_URL}#{section}"


def check_constructor_arguments(positional: tuple[object, ...], keywords: dict[str, object]) -> None:
    if positional:
        raise TypeError(
            migration_message(
                "Only width, height, and face_percent may be positional. "
                "The old padding/fix_gamma positions were removed; use resize=False as a keyword.",
                "python-arguments",
            )
        )
    removed = set(keywords) & {"padding", "fix_gamma", "detector"}
    if removed:
        raise TypeError(
            migration_message(
                f"Removed Cropper argument(s): {', '.join(sorted(removed))}. "
                "Use face_percent for crop margins; apply any brightness adjustment after cropping. "
                "Detector selection and automatic gamma correction were removed.",
                "python-arguments",
            )
        )
    if keywords:
        name = next(iter(keywords))
        raise TypeError(f"Cropper.__init__() got an unexpected keyword argument {name!r}")


def check_crop_arguments(positional: tuple[object, ...], keywords: dict[str, object]) -> None:
    if positional or "diagnostics" in keywords:
        raise TypeError(
            migration_message(
                "crop() accepts only the source image; there is no diagnostics flag. "
                "Use result = cropper.crop(source), then result.image and result.diagnostics.",
                "python-results",
            )
        )
    if keywords:
        name = next(iter(keywords))
        raise TypeError(f"Cropper.crop() got an unexpected keyword argument {name!r}")


def removed_module_attribute(module: str, name: str, replacements: dict[str, tuple[str, str]]) -> NoReturn:
    """Keep migration guidance in ImportError instead of losing it during a from-import."""
    if name in replacements:
        advice, section = replacements[name]
        raise ImportError(migration_message(f"{module}.{name} was removed. {advice}", section))
    raise AttributeError(f"module {module!r} has no attribute {name!r}")


REMOVED_OPTIONS = {
    "-i": "directory-mode",
    "--input": "directory-mode",
    "-r": "directory-mode",
    "--reject": "directory-mode",
    "--no-confirm": "directory-mode",
    "--skip-prompt": "directory-mode",
    "-e": "output-format",
    "--extension": "output-format",
    "--detector": "different-results",
}
OPTION_VALUES = {"-o", "--output", "-p", "--path", "-w", "--width", "-H", "--height", "--facePercent", "--json"}


def _removed_short_option(token: str) -> tuple[str | None, bool]:
    """Inspect flag clusters without treating an attached output filename as flags."""
    if not token.startswith("-") or token.startswith("--"):
        return None, False
    for index, character in enumerate(token[1:], start=1):
        option = f"-{character}"
        if option in REMOVED_OPTIONS:
            return option, False
        if option in OPTION_VALUES:
            return None, index == len(token) - 1
        if option not in {"-n", "-v", "-V", "-h"}:
            break
    return None, False


def removed_cli_option(args: list[str]) -> tuple[str, str] | None:
    """Recognize removed flags before argparse mistakes their value for a source."""
    skip_value = False
    for token in args:
        if skip_value:
            skip_value = False
            continue
        if token == "--":
            break
        option = token.split("=", 1)[0]
        if option in REMOVED_OPTIONS:
            return option, REMOVED_OPTIONS[option]
        short_option, needs_value = _removed_short_option(token)
        if short_option is not None:
            return short_option, REMOVED_OPTIONS[short_option]
        skip_value = token in OPTION_VALUES or needs_value
    return None


def removed_option_message(option: str, section: str) -> str:
    advice = {
        "directory-mode": "Pass one image as a positional argument; use a shell loop for batches.",
        "output-format": "Choose the format with an output filename, e.g. -o cropped.png.",
        "different-results": "Detector selection was removed; the built-in detector is used automatically.",
    }
    return migration_message(f"{option} was removed. {advice[section]}", section)
