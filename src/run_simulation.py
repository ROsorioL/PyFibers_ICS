"""Run a PyFibers simulation of a femoral nerve fiber stimulated by COMSOL-derived
extracellular potentials from an interferential current (IFC) field.

This is a starting template — adjust fiber model parameters and stimulus waveform
to match your femoral nerve / IFC protocol.
"""

from __future__ import annotations

import argparse

import numpy as np
from pyfibers import build_fiber, FiberModel  # adjust import to match installed PyFibers API

from load_comsol_potentials import load_field, interpolate_to_fiber


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--comsol-file", required=True, help="Path to COMSOL potential export")
    parser.add_argument("--fiber-diameter", type=float, default=10.0, help="Fiber diameter (um)")
    parser.add_argument("--n-nodes", type=int, default=51, help="Number of fiber nodes")
    args = parser.parse_args()

    # 1. Build the femoral nerve fiber model
    fiber = build_fiber(
        model=FiberModel.MRG,  # example: MRG model; pick the model matching your femoral nerve fiber type
        diameter=args.fiber_diameter,
        n_nodes=args.n_nodes,
    )

    # 2. Load COMSOL IFC field and interpolate potentials onto fiber coordinates
    field = load_field(args.comsol_file)
    potentials = interpolate_to_fiber(field, fiber.coordinates)

    # 3. Apply extracellular potentials as the stimulus and run
    fiber.apply_extracellular_potentials(potentials)
    results = fiber.run()

    np.save("results/membrane_voltages.npy", results.membrane_voltages)
    print(f"Simulation complete. Threshold: {results.threshold}")


if __name__ == "__main__":
    main()
