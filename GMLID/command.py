from typing import Sequence
import argparse


def parse_args(args: Sequence[str] | None = None):
    parser = argparse.ArgumentParser(
        "GMLID",
        "Gravitational Lensing Interactive Demo for thin-lens simulations",
        allow_abbrev=True,
    )

    parser.add_argument("--launch", action="store_true", help="Launch the real-time demo")

    arguments = parser.parse_args(args)
    return arguments
