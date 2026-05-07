"""Minimal HDF5 mapping reader.

This module provides a small solver-agnostic helper for reading HDF5 files by
attribute-to-dataset-path mapping.
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

import h5py
import numpy as np


class H5MapReader:
    """Read an HDF5 file through a logical-name to dataset-path mapping.

    Parameters
    ----------
    h5_path:
        Path to the HDF5 file.
    mapping:
        Mapping from exposed attribute names to HDF5 dataset paths.
    cache:
        When true, cache values returned through mapped lookups.
    as_array:
        When true, eagerly convert HDF5 datasets to in-memory numpy/Python
        objects. When false, return h5py dataset/group objects directly.
    """

    def __init__(
        self,
        h5_path: str | Path,
        mapping: Mapping[str, str] | None = None,
        *,
        cache: bool = True,
        as_array: bool = True,
    ) -> None:
        self.h5_path = Path(h5_path)
        self.mapping = dict(mapping or {})
        self.cache = cache
        self.as_array = as_array
        self._cache: dict[str, Any] = {}
        self._f = h5py.File(self.h5_path, "r")

    def __enter__(self) -> "H5MapReader":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def __del__(self) -> None:
        try:
            self.close()
        except Exception:
            pass

    def __getattr__(self, name: str) -> Any:
        if name in self.mapping:
            return self.get(name)
        raise AttributeError(f"{type(self).__name__!s} has no attribute {name!r}")

    def __contains__(self, name: str) -> bool:
        return name in self.mapping

    def keys(self) -> tuple[str, ...]:
        return tuple(self.mapping.keys())

    def get(self, name: str, default: Any = None) -> Any:
        """Return the mapped value for *name* or *default* if not mapped."""
        if name not in self.mapping:
            return default

        if self.cache and name in self._cache:
            return self._cache[name]

        value = self._get_mapped_value(name)
        if self.cache:
            self._cache[name] = value
        return value

    def clear_cache(self) -> None:
        self._cache.clear()

    def close(self) -> None:
        if hasattr(self, "_f") and self._f:
            try:
                if self._f.id.valid:
                    self._f.close()
            finally:
                self._f = None

    def print_structure(self) -> None:
        """Print the HDF5 tree rooted at the file object."""

        def _walk(name: str, obj: h5py.Dataset | h5py.Group) -> None:
            kind = "group" if isinstance(obj, h5py.Group) else "dataset"
            print(f"{name} [{kind}]")

        self._f.visititems(_walk)

    def read_path(self, path: str) -> Any:
        """Read a raw HDF5 path without consulting the logical mapping."""
        obj = self._get_obj(path)
        if not self.as_array:
            return obj
        return self._materialize(obj)

    def _get_mapped_value(self, name: str) -> Any:
        path = self.mapping[name]
        return self.read_path(path)

    def _get_obj(self, path: str) -> h5py.Dataset | h5py.Group:
        return self._f[path]

    def _read_dataset(self, path: str) -> Any:
        obj = self._get_obj(path)
        if not isinstance(obj, h5py.Dataset):
            raise TypeError(f"HDF5 path {path!r} is not a dataset.")
        return obj[()]

    def _materialize(self, obj: h5py.Dataset | h5py.Group) -> Any:
        if isinstance(obj, h5py.Group):
            return obj

        data = obj[()]
        return self._normalize_value(data)

    def _normalize_value(self, value: Any) -> Any:
        if isinstance(value, bytes):
            return value.decode("utf-8", errors="replace")

        if isinstance(value, np.ndarray):
            if value.dtype.kind in {"S", "O", "U"}:
                return self._maybe_decode_strings(value)
            if value.shape == ():
                return value.item()
            return value

        if isinstance(value, np.generic):
            return value.item()

        return value

    def _decode_array(self, value: np.ndarray) -> Any:
        decoded = np.array(
            [
                item.decode("utf-8", errors="replace") if isinstance(item, bytes) else item
                for item in value.flat
            ],
            dtype=object,
        ).reshape(value.shape)

        if decoded.shape == ():
            return decoded.item()
        return decoded

    def _maybe_decode_strings(self, value: Any) -> Any:
        if isinstance(value, bytes):
            return value.decode("utf-8", errors="replace")
        if isinstance(value, np.ndarray) and value.dtype.kind in {"S", "O", "U"}:
            return self._decode_array(value)
        return value
