"""Generate interferential current (IFC) stimulation waveforms.

Classic IFC uses two independent electrode pairs ("channels"), each driven by a
medium-frequency sinusoidal current (e.g. ~4 kHz). The two carrier frequencies
differ slightly (e.g. 4000 Hz and 4100 Hz); where their fields overlap in tissue,
the superposed currents produce an amplitude-modulated "beat" at the difference
frequency (here 100 Hz) — the physiologically relevant low-frequency envelope.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class IFCParams:
    f1: float = 4000.0       # channel 1 carrier frequency (Hz)
    f2: float = 4100.0       # channel 2 carrier frequency (Hz)
    amplitude: float = 1.0   # peak current amplitude per channel (mA)
    duration: float = 0.05   # total stimulus duration (s)
    dt: float = 1.0e-5       # time step (s) -- must resolve the carrier (>= ~20x f2)

    @property
    def beat_frequency(self) -> float:
        return abs(self.f2 - self.f1)


def generate_ifc_currents(params: IFCParams) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Generate the two channel current waveforms and the time vector.

    Returns:
        t:  (T,) time vector (s)
        i1: (T,) channel 1 current waveform (mA), carrier f1
        i2: (T,) channel 2 current waveform (mA), carrier f2
    """
    t = np.arange(0.0, params.duration, params.dt)
    i1 = params.amplitude * np.sin(2 * np.pi * params.f1 * t)
    i2 = params.amplitude * np.sin(2 * np.pi * params.f2 * t)
    return t, i1, i2


def beat_envelope(t: np.ndarray, params: IFCParams) -> np.ndarray:
    """Analytic amplitude envelope of the interference pattern at the beat frequency."""
    return params.amplitude * np.abs(np.cos(np.pi * params.beat_frequency * t))
