"""Low-level Genesis HDF5 reader helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Mapping

import h5py

from postpro.io.hdf5 import H5MapReader


def read_genesis_version(path: str | Path) -> int:
    """Return the Genesis major version encoded in an HDF5 file."""
    with h5py.File(path, "r") as handle:
        return int(handle["Meta"]["Version"]["Major"][0])


class GenesisH5File(H5MapReader):
    """Common HDF5 reader base for Genesis file variants."""

    expected_suffix: str = ""
    supported_version: int = 4

    def __init__(
        self,
        h5_path: str | Path,
        mapping: Mapping[str, str],
        *,
        cache: bool = True,
        as_array: bool = True,
    ) -> None:
        path = Path(h5_path)
        if self.expected_suffix and not path.name.endswith(self.expected_suffix):
            raise ValueError(
                f"{type(self).__name__} filename must end with {self.expected_suffix!r}"
            )

        version = read_genesis_version(path)
        if version != self.supported_version:
            raise ValueError(f"Unsupported Genesis version {version}")

        self.version = version
        super().__init__(path, mapping=mapping, cache=cache, as_array=as_array)
