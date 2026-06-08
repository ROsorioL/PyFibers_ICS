"""Visualize IFC stimulus and PyFibers simulation outputs.

Produces:
  - IFC channel currents and beat envelope over time
  - Space-time extracellular potential heatmap (Ve(x, t))
  - Membrane voltage traces from the fiber simulation
"""

from __future__ import annotations

import argparse

import matplotlib.pyplot as plt
import numpy as np

from ifc_waveform import IFCParams, beat_envelope, generate_ifc_currents


def plot_waveform(params: IFCParams, out_path: str) -> None:
    t, i1, i2 = generate_ifc_currents(params)
    envelope = beat_envelope(t, params)

    fig, axes = plt.subplots(2, 1, sharex=True, figsize=(9, 6))
    axes[0].plot(t * 1e3, i1, label=f"Channel 1 ({params.f1:.0f} Hz)", alpha=0.7)
    axes[0].plot(t * 1e3, i2, label=f"Channel 2 ({params.f2:.0f} Hz)", alpha=0.7)
    axes[0].set_ylabel("Current (A)")
    axes[0].legend()
    axes[0].set_title("IFC channel currents")

    axes[1].plot(t * 1e3, i1 + i2, color="0.4", alpha=0.6, label="Superposed current")
    axes[1].plot(t * 1e3, envelope, color="crimson", lw=2, label=f"Beat envelope ({params.beat_frequency:.0f} Hz)")
    axes[1].plot(t * 1e3, -envelope, color="crimson", lw=2)
    axes[1].set_xlabel("Time (ms)")
    axes[1].set_ylabel("Current (A)")
    axes[1].legend()
    axes[1].set_title("Interference pattern")

    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def plot_ve_heatmap(ve_path: str, time_path: str, out_path: str) -> None:
    ve_matrix = np.load(ve_path)
    t = np.load(time_path)

    fig, ax = plt.subplots(figsize=(9, 4))
    im = ax.pcolormesh(t * 1e3, np.arange(ve_matrix.shape[0]), ve_matrix, shading="auto", cmap="RdBu_r")
    ax.set_xlabel("Time (ms)")
    ax.set_ylabel("Fiber node index")
    ax.set_title("Extracellular potential Ve(x, t)")
    fig.colorbar(im, ax=ax, label="Potential (V)")
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def plot_membrane_voltages(voltages_path: str, time_path: str, out_path: str) -> None:
    voltages = np.load(voltages_path)
    t = np.load(time_path)

    fig, ax = plt.subplots(figsize=(9, 4))
    for node_idx in range(0, voltages.shape[0], max(1, voltages.shape[0] // 8)):
        ax.plot(t[: voltages.shape[1]] * 1e3, voltages[node_idx], label=f"Node {node_idx}")
    ax.set_xlabel("Time (ms)")
    ax.set_ylabel("Membrane voltage (mV)")
    ax.set_title("Fiber membrane response")
    ax.legend(fontsize="small")
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results-dir", default="results")
    args = parser.parse_args()
    d = args.results_dir

    params = IFCParams()
    plot_waveform(params, f"{d}/ifc_waveform.png")
    plot_ve_heatmap(f"{d}/ve_matrix.npy", f"{d}/time_vector.npy", f"{d}/ve_heatmap.png")
    plot_membrane_voltages(f"{d}/membrane_voltages.npy", f"{d}/time_vector.npy", f"{d}/membrane_voltages.png")
    print(f"Plots saved to {d}/")


if __name__ == "__main__":
    main()
