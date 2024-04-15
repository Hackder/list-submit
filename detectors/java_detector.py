import glob
import os

from detectors.detector import Detector, DetectionResult, is_program_file


def get_detector() -> Detector:
    return Detector(
        name="Python",
        detect=get_probability_with_files,
    )


def get_probability_with_files(path: str) -> DetectionResult:
    first_files = os.listdir(path)

    if "src" in first_files:
        path = os.path.join(path, "src")

    files = glob.glob(os.path.join(path, "**", "*"), recursive=True)
    files = [f for f in files if is_program_file(f)]
    java_files = [f for f in files if f.endswith(".java")]

    if len(java_files) / len(files) > 0.5:
        non_test_files = [
            f
            for f in java_files
            if not f.endswith("Test.java") and not f.startswith("Test")
        ]
        return (0.5, non_test_files, [])

    return (0.0, [], [])
