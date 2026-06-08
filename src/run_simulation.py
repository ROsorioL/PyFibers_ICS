"""Run a PyFibers simulation of a femoral nerve fiber stimulated by an interferential
current (IFC) field whose spatial distribution comes from COMSOL exports.

Pipeline:
  1. Build the femoral nerve fiber model in PyFibers.
  2. Load the two COMSOL electrode-pair potential fields and interpolate onto fiber nodes.
  3. Generate the two IFC channel current waveforms (carriers f1, f2 -> beat at |f2-f1|).
  4. Superpose into a space-time extracellular potential matrix Ve(x, t).
  5. Apply Ve(x, t) as the extracellular stimulus and run the PyFibers simulation.

Adjust the PyFibers calls (model choice, stimulus application, run/threshold API) to
match the version of PyFibers you have installed -- see https://pyfibers.readthedocs.io
"""

from __future__ import annotations

import argparse

import numpy as np
from pyfibers import build_fiber, FiberModel

from build_extracellular_potentials import build_ve_matrix
from ifc_waveform import IFCParams, generate_ifc_currents
from load_comsol_potentials import load_channel_potentials


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--channel1-file", required=True, help="COMSOL export: electrode pair 1 unit-current potential field")
    parser.add_argument("--channel2-file", required=True, help="COMSOL export: electrode pair 2 unit-current potential field")
    parser.add_argument("--fiber-diameter", type=float, default=10.0, help="Fiber diameter (um)")
    parser.add_argument("--n-nodes", type=int, default=51, help="Number of fiber nodes of Ranvier")
    parser.add_argument("--f1", type=float, default=4000.0, help="Channel 1 carrier frequency (Hz)")
    parser.add_argument("--f2", type=float, default=4100.0, help="Channel 2 carrier frequency (Hz)")
    parser.add_argument("--amplitude", type=float, default=1.0e-3, help="Peak current amplitude per channel (A)")
    parser.add_argument("--duration", type=float, default=0.05, help="Stimulus duration (s)")
    parser.add_argument("--dt", type=float, default=1.0e-5, help="Time step (s)")
    parser.add_argument("--out", default="results/membrane_voltages.npy", help="Output file for membrane voltages")
    args = parser.parse_args()

    # 1. Build the femoral nerve fiber model (e.g. MRG double-cable model for myelinated fibers)
    fiber = build_fiber(
        model=FiberModel.MRG,
        diameter=args.fiber_diameter,
        n_nodes=args.n_nodes,
    )

    # 2. Load COMSOL fields for each electrode-pair channel and interpolate onto fiber nodes
    v1, v2 = load_channel_potentials(args.channel1_file, args.channel2_file, fiber.coordinates)

    # 3. Generate IFC channel current waveforms
    ifc_params = IFCParams(
        f1=args.f1, f2=args.f2, amplitude=args.amplitude, duration=args.duration, dt=args.dt
    )
    t, i1, i2 = generate_ifc_currents(ifc_params)
    print(f"Beat frequency at target tissue: {ifc_params.beat_frequency:.1f} Hz")

    # 4. Superpose spatial fields with channel currents -> space-time extracellular potential
    ve_matrix = build_ve_matrix(v1, v2, i1, i2)

    # 5. Apply the time-varying extracellular potential to the fiber and run
    fiber.apply_extracellular_potentials(ve_matrix, dt=ifc_params.dt)
    results = fiber.run()

    np.save(args.out, results.membrane_voltages)
    np.save("results/time_vector.npy", t)
    np.save("results/ve_matrix.npy", ve_matrix)
    print(f"Simulation complete. Output saved to {args.out}")
    print(f"Activation threshold: {results.threshold}")


if __name__ == "__main__":
    main()
