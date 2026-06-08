"""Load extracellular potential fields exported from COMSOL and interpolate onto fiber coordinates.

An IFC simulation needs one spatial field per electrode pair/channel: COMSOL solves the
(quasi-)static field for unit current injected by each pair independently (lead-field /
reciprocity approach), and the time-domain potential at a point is then the linear
superposition `V(x, t) = V_channel1(x) * I1(t) + V_channel2(x) * I2(t)`.

Expected COMSOL export: CSV/TXT with columns for spatial coordinates (x, y, z) and the
extracellular potential per unit current V, e.g. one row per mesh/grid point. Adjust
`COLUMNS` to match your actual COMSOL export header (Export > Data in COMSOL).
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.interpolate import griddata

COLUMNS = ["x", "y", "z", "V"]


def load_field(path: str) -> pd.DataFrame:
    """Read a COMSOL export file into a DataFrame with columns x, y, z, V (SI units, V per unit A)."""
    return pd.read_csv(path, comment="%", names=COLUMNS, header=None)


def interpolate_to_fiber(field: pd.DataFrame, fiber_coords: np.ndarray) -> np.ndarray:
    """Interpolate a COMSOL potential field onto fiber node coordinates.

    Args:
        field: DataFrame with columns x, y, z, V from `load_field`.
        fiber_coords: (N, 3) array of fiber node coordinates, same units/frame as the COMSOL export.

    Returns:
        (N,) array of unit-current extracellular potentials at each fiber node.
    """
    points = field[["x", "y", "z"]].to_numpy()
    values = field["V"].to_numpy()
    interpolated = griddata(points, values, fiber_coords, method="linear")
    # Fall back to nearest-neighbor for any points outside the convex hull of the COMSOL mesh
    nan_mask = np.isnan(interpolated)
    if np.any(nan_mask):
        interpolated[nan_mask] = griddata(points, values, fiber_coords[nan_mask], method="nearest")
    return interpolated


def load_channel_potentials(channel1_path: str, channel2_path: str, fiber_coords: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Load and interpolate the two IFC electrode-pair fields onto fiber coordinates.

    Returns:
        v1, v2: (N,) unit-current potentials at each fiber node for channel 1 and channel 2.
    """
    v1 = interpolate_to_fiber(load_field(channel1_path), fiber_coords)
    v2 = interpolate_to_fiber(load_field(channel2_path), fiber_coords)
    return v1, v2
