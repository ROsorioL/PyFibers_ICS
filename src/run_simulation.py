"""Run a PyFibers simulation of a femoral nerve fiber stimulated by an interferential
current (IFC) field whose spatial distribution comes from COMSOL exports.

Verified against pyfibers 0.8.5 / NEURON 9.0.1 (installed in WSL Ubuntu venv at
/root/pyfibers_env). Real PyFibers usage:

  fiber = build_fiber(fiber_model=FiberModel.MRG_INTERPOLATION, diameter=..., n_nodes=...)
  fiber.potentials = <(N,) array of unit-amplitude potentials per source, in mV>
  stim = ScaledStim(waveform=<callable(t_ms) -> float>, dt=..., tstop=...)
  ap, ap_time = stim.run_sim(stimamp=<scale factor>, fiber=fiber)

For multiple sources (our two IFC channels), `potentials` takes a list of (N,) arrays
(one per source/channel) and `waveform` a matching list of callables; `stimamp` can be
a matching list of per-source scale factors.

Pipeline:
  1. Build the femoral nerve fiber model in PyFibers.
  2. Load the two COMSOL electrode-pair potential fields and interpolate onto fiber nodes
     (these become the two "sources").
  3. Build the two IFC channel waveform callables (carriers f1, f2 -> beat at |f2-f1|).
  4. Assign `fiber.potentials` (list of per-source spatial fields) and run via ScaledStim.
"""

from __future__ import annotations

import argparse

import numpy as np
from pyfibers import build_fiber, FiberModel, ScaledStim

from ifc_waveform import IFCParams
from load_comsol_potentials import load_channel_potentials


def make_waveform(frequency_hz: float):
    """Return a callable waveform(t_ms) -> float for a sinusoidal IFC channel carrier."""

    def waveform(t_ms: float) -> float:
        return float(np.sin(2 * np.pi * frequency_hz * (t_ms * 1e-3)))

    return waveform


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--channel1-file", required=True, help="COMSOL export: electrode pair 1 unit-current potential field")
    parser.add_argument("--channel2-file", required=True, help="COMSOL export: electrode pair 2 unit-current potential field")
    parser.add_argument("--fiber-model", default="MRG_INTERPOLATION", help="PyFibers FiberModel name (e.g. MRG_INTERPOLATION)")
    parser.add_argument("--fiber-diameter", type=float, default=10.0, help="Fiber diameter (um)")
    parser.add_argument("--n-nodes", type=int, default=51, help="Number of fiber nodes of Ranvier")
    parser.add_argument("--f1", type=float, default=4000.0, help="Channel 1 carrier frequency (Hz)")
    parser.add_argument("--f2", type=float, default=4100.0, help="Channel 2 carrier frequency (Hz)")
    parser.add_argument("--amplitude1", type=float, default=1.0, help="Channel 1 stimamp scale factor (mA)")
    parser.add_argument("--amplitude2", type=float, default=1.0, help="Channel 2 stimamp scale factor (mA)")
    parser.add_argument("--tstop", type=float, default=50.0, help="Simulation duration (ms)")
    parser.add_argument("--dt", type=float, default=0.001, help="Time step (ms)")
    args = parser.parse_args()

    # 1. Build the femoral nerve fiber model (default: MRG double-cable myelinated fiber)
    fiber_model = getattr(FiberModel, args.fiber_model)
    fiber = build_fiber(fiber_model=fiber_model, diameter=args.fiber_diameter, n_nodes=args.n_nodes)
    print(f"Built fiber: {fiber_model.name}, {len(fiber.coordinates)} coordinates")

    # 2. Load COMSOL fields for each electrode-pair channel and interpolate onto fiber nodes.
    #    These become the two stimulation "sources" (one per IFC channel).
    v1, v2 = load_channel_potentials(args.channel1_file, args.channel2_file, fiber.coordinates)
    fiber.potentials = [v1, v2]

    # 3. Build the IFC channel waveforms (carriers f1, f2 -> interference beat at |f2-f1|)
    ifc_params = IFCParams(f1=args.f1, f2=args.f2)
    print(f"Beat frequency at target tissue: {ifc_params.beat_frequency:.1f} Hz")
    waveforms = [make_waveform(args.f1), make_waveform(args.f2)]

    # 4. Run the simulation: ScaledStim multiplies each source's potentials by its waveform
    #    and the corresponding stimamp scale factor, then sums them (superposition).
    stim = ScaledStim(waveform=waveforms, dt=args.dt, tstop=args.tstop)
    ap, ap_time = stim.run_sim(stimamp=[args.amplitude1, args.amplitude2], fiber=fiber)

    print(f"Action potential detected: {bool(ap)} (count={ap}), at t = {ap_time} ms")


if __name__ == "__main__":
    main()
