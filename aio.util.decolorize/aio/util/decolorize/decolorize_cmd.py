
import sys
from typing import Optional

from .decolorize import DecolorizeRunner


def main(*args: str) -> Optional[int]:
    return DecolorizeRunner(*args)()


def decolorize_cmd() -> None:
    sys.exit(main(*sys.argv[1:]))


if __name__ == "__main__":
    decolorize_cmd()
