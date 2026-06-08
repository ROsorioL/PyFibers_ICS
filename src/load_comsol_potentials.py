"""Load extracellular potential field exported from COMSOL and interpolate onto fiber coordinates.

Expected COMSOL export: a CSV/TXT with columns for spatial coordinates (x, y, z) and the
extracellular potential V, e.g. one row per mesh/grid point. Adjust `COLUMNS` to match
your actual COMSOL export header.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.interpolate import griddata

COLUMNS = ["x", "y", "z", "V"]


def load_field(path: str) -> pd.DataFrame:
    """Read a COMSOL export file into a DataFrame with columns x, y, z, V (SI units)."""
    df = pd.read_csv(path, comment="%", names=COLUMNS, header=None)
    return df


def interpolate_to_fiber(field: pd.DataFrame, fiber_coords: np.ndarray) -> np.ndarray:
    """Interpolate the COMSOL potential field onto fiber node coordinates.

    Args:
        field: DataFrame with columns x, y, z, V from `load_field`.
        fiber_coords: (N, 3) array of fiber node coordinates in the same units/frame as the COMSOL export.

    Returns:
        (N,) array of extracellular potentials at each fiber node.
    """
    points = field[["x", "y", "z"]].to_numpy()
    values = field["V"].to_numpy()
    return griddata(points, values, fiber_coords, method="linear")
