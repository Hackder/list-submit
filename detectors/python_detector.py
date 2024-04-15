import os

from detectors.detector import Detector, DetectionResult


def get_detector() -> Detector:
    return Detector(
        name="Python",
        detect=get_probability_with_files,
    )


def get_probability_with_files(path: str) -> DetectionResult:
    files = os.listdir(path)

    if "src" in files:
        files = [
            os.path.join("src", filename)
            for filename in os.listdir(os.path.join(path, "src"))
        ]

    if "riesenie.py" in files:
        if __has_list_header_comment(os.path.join(path, "riesenie.py")):
            return (0.9, ["riesenie.py"], [])
        return (
            0.8,
            ["riesenie.py"],
            ["File `riesenie.py` is missing a header comment."],
        )

    if "src/riesenie.py" in files:
        if __has_list_header_comment(os.path.join(path, "src/riesenie.py")):
            return (0.9, ["src/riesenie.py"], [])

        return (
            0.8,
            ["src/riesenie.py"],
            ["File `src/riesenie.py` is missing a header comment."],
        )

    python_files = [f for f in files if f.endswith(".py")]
    if len(python_files) == len(files):
        return (0.8, python_files, [])

    if len(python_files) / len(files) > 0.5:
        return (0.5, python_files, [])

    if len(python_files) > 0:
        return (0.3, python_files, [])

    return (0.0, [], [])


def __has_list_header_comment(file_path: str) -> bool:
    with open(file_path) as f:
        lines = f.readlines()[:3]
    return (
        len(lines) == 3
        and lines[0].startswith("#")
        and lines[1].startswith("# autor")
        and lines[2].startswith("# datum")
    )
