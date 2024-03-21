import sys
from typing import Any

# A unit object used for default argument values,
# to prevent unintended collisions with provided values
__UNIT = object()


def error(message: str, context: Any = __UNIT) -> None:
    print(message, file=sys.stderr)
    if context is not __UNIT:
        print(context, file=sys.stderr)
