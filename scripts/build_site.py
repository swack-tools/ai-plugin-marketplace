"""Build the static marketplace from immutable source inputs."""
import argparse
from pathlib import Path


def arguments():
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument('--live', action='store_true')
    modes.add_argument('--offline', type=Path)
    parser.add_argument('--registry', type=Path, default=Path('catalog/projects.json'))
    parser.add_argument('--output', type=Path, default=Path('build/site'))
    return parser.parse_args()


if __name__ == '__main__':
    arguments()
