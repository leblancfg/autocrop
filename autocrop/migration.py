"""Actionable messages for calls that used the v1 interface."""

FAQ_URL = "https://leblancfg.com/autocrop/faq/"


def migration_message(message: str, section: str) -> str:
    return f"autocrop 2: {message} See {FAQ_URL}#{section}"


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
        if token[:2] in {"-i", "-r", "-e"}:
            return token[:2], REMOVED_OPTIONS[token[:2]]
        skip_value = token in OPTION_VALUES
    return None


def removed_option_message(option: str, section: str) -> str:
    advice = {
        "directory-mode": "Pass one image as a positional argument; use a shell loop for batches.",
        "output-format": "Choose the format with an output filename, e.g. -o cropped.png.",
        "different-results": "Detector selection was removed; the built-in detector is used automatically.",
    }
    return migration_message(f"{option} was removed. {advice[section]}", section)
