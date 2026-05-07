from __future__ import annotations

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
paramstudy_src = Path(__file__).resolve().parents[2] / "paramstudy" / "src"
if paramstudy_src.is_dir():
    sys.path.insert(0, str(paramstudy_src))

from postpro.api.genesis import (
    render_pulse_metrics,
    render_slice_diagnostics,
    render_spectrum,
    render_zoverview,
)


DEFAULT_INPUT = Path("/home/duoxup/simdata/pitz/S2E_ideal_machine/case1/g4.000.out.h5")
DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parents[1] / "outputs" / "genesis_case1_viz"


def main(input_path: Path = DEFAULT_INPUT, output_dir: Path = DEFAULT_OUTPUT_DIR) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    saved: list[Path] = []

    saved.append(_save_render(render_zoverview, input_path, output_dir / "z_overview.png"))
    saved.append(_save_render(render_pulse_metrics, input_path, output_dir / "pulse_metrics.png"))
    saved.append(_save_render(render_slice_diagnostics, input_path, output_dir / "slice_profiles.png"))
    saved.append(_save_render(render_spectrum, input_path, output_dir / "spectrum.png"))
    return saved


def _save_render(render_fn, input_path: Path, output_path: Path) -> Path:
    fig, _axes = render_fn(input_path, save_to=output_path)
    plt.close(fig)
    return output_path


if __name__ == "__main__":
    saved = main()
    for path in saved:
        print(path)
