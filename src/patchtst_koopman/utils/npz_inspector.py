"""Dump the structure of an NPZ file (shapes, dtypes, basic stats, first rows).

Installed as the ``inspect-npz`` console script via ``pyproject.toml``:

    inspect-npz data/experiment_006/test.npz
"""
import argparse
import sys

import numpy as np


def inspect_npz(file_path):
    """Print a per-array summary of the given NPZ file."""
    print("=" * 80)
    print(f"NPZ file: {file_path}")
    print("=" * 80)

    try:
        data = np.load(file_path)
    except FileNotFoundError:
        print(f"ERROR: file not found: {file_path}")
        return 1
    except Exception as exc:
        print(f"ERROR: failed to load NPZ: {exc}")
        return 1

    keys = list(data.keys())
    print(f"\nKeys: {keys}")
    print(f"Total arrays: {len(keys)}\n")

    for key in keys:
        arr = data[key]
        print("-" * 80)
        print(f"Key: {key}")
        print(f"  shape: {arr.shape}")
        print(f"  dtype: {arr.dtype}")
        print(f"  size:  {arr.size} elements")
        print(f"  bytes: {arr.nbytes / 1024:.2f} KB")

        if np.issubdtype(arr.dtype, np.number):
            print(f"  min:   {np.min(arr):.6f}")
            print(f"  max:   {np.max(arr):.6f}")
            print(f"  mean:  {np.mean(arr):.6f}")
            print(f"  std:   {np.std(arr):.6f}")

        print("  head:")
        if arr.ndim == 1:
            print(f"    {arr[:5]}")
        elif arr.ndim == 2:
            print(f"    {arr[:5, :]}")
        else:
            print(f"    {arr.flat[:5]}")

    print("\n" + "=" * 80)
    return 0


def main():
    parser = argparse.ArgumentParser(
        description="Inspect the structure of an NPZ file"
    )
    parser.add_argument("file", help="Path to the .npz file to inspect")
    args = parser.parse_args()
    sys.exit(inspect_npz(args.file))


if __name__ == "__main__":
    main()
