"""Combine COMSOL spatial fields with IFC time-domain currents into Ve(x, t).

By superposition (linear quasi-static media), the extracellular potential at fiber
node x and time t is:

    Ve(x, t) = V1(x) * I1(t) + V2(x) * I2(t)

where V1, V2 are the per-unit-current spatial potentials from COMSOL (one per
electrode-pair channel), and I1(t), I2(t) are the IFC channel current waveforms.
"""

from __future__ import annotations

import numpy as np


def build_ve_matrix(v1: np.ndarray, v2: np.ndarray, i1: np.ndarray, i2: np.ndarray) -> np.ndarray:
    """Build the full space-time extracellular potential matrix.

    Args:
        v1, v2: (N,) unit-current spatial potentials at each fiber node (V/A) for channels 1 & 2.
        i1, i2: (T,) channel current waveforms (A) over time.

    Returns:
        (N, T) extracellular potential at each fiber node over time (V).
    """
    return np.outer(v1, i1) + np.outer(v2, i2)
