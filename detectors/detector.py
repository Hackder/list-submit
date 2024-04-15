from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, TypeAlias

DetectionResult: TypeAlias = tuple[float, list[str], list[str]]


@dataclass
class Detector:
    name: str

    detect: Callable[[str], DetectionResult]
    """
    Looks at the provided directory and returns the probability that the direcotry
    contains a python solution to a list problem, along with the files it things,
    are part of the solution.

    Returns:
        (probability, files, recommendations)
    """
