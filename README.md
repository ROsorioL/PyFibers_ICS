# PyFibers ICS — Femoral Nerve Interferential Current Stimulation

Simulation of a femoral nerve fiber model in [PyFibers](https://pyfibers.readthedocs.io/), driven by
extracellular potentials generated from an interferential current stimulation (IFC) field model in COMSOL.

## Pipeline

Interferential current (IFC) stimulation uses two electrode-pair channels driven at slightly
different medium-frequency carriers (e.g. 4000 Hz and 4100 Hz). Where their fields overlap in
tissue, the currents superpose into an amplitude-modulated "beat" at the difference frequency
(e.g. 100 Hz) — the physiologically relevant low-frequency envelope that drives nerve activation.

1. **COMSOL**: Solve the field independently for each electrode-pair channel (unit current /
   reciprocity, stationary study), and export each spatial potential distribution (CSV/TXT) to
   [comsol_exports/](comsol_exports/) — one file per channel.
2. **Loader** ([src/load_comsol_potentials.py](src/load_comsol_potentials.py)): reads both COMSOL
   exports and interpolates each onto the femoral nerve fiber's spatial coordinates (`v1`, `v2`).
3. **IFC waveform** ([src/ifc_waveform.py](src/ifc_waveform.py)): defines the IFC carrier
   parameters (`f1`, `f2`) and the resulting beat frequency `|f2 - f1|`.
4. **PyFibers** ([src/run_simulation.py](src/run_simulation.py)): builds the femoral nerve fiber
   model, assigns `fiber.potentials = [v1, v2]` as the two stimulation sources, drives them with
   sinusoidal waveforms at `f1`/`f2` via `pyfibers.ScaledStim` (which performs the superposition
   internally), and runs the simulation, reporting whether/when an action potential occurs.

> See [docs/tutorial.md](docs/tutorial.md) ([PDF](docs/tutorial.pdf)) for a full step-by-step
> walkthrough, and [docs/documentation.md](docs/documentation.md) ([PDF](docs/documentation.pdf))
> for the requirements reference and line-by-line code documentation.

## Project layout

```
comsol_exports/   Raw COMSOL field exports (potentials vs. spatial coordinates)
src/              Python source: COMSOL loader + PyFibers simulation scripts
notebooks/        Exploratory analysis / visualization notebooks
results/          Simulation outputs and figures
docs/             Notes on the COMSOL model setup and simulation parameters
```

## Setup

PyFibers depends on [NEURON](https://www.neuron.yale.edu/neuron/), which does not ship Windows
wheels on PyPI. **Use WSL (Ubuntu)** for a working environment:

```bash
wsl --install            # one-time, requires reboot
wsl -d Ubuntu

# inside WSL Ubuntu:
sudo apt-get update && sudo apt-get install -y python3-venv python3-pip build-essential
python3 -m venv ~/pyfibers_env
source ~/pyfibers_env/bin/activate
pip install pyfibers numpy scipy pandas matplotlib neuron

# compile NEURON mechanisms bundled with PyFibers (one-time)
python -c "import pyfibers; print(pyfibers.MOD_dir)"
cd <path-printed-above> && nrnivmodl
```

This setup was verified end-to-end with `pyfibers==0.8.5` and `neuron==9.0.1`.

## Usage

```bash
python src/run_simulation.py \
    --channel1-file comsol_exports/channel1_field.csv \
    --channel2-file comsol_exports/channel2_field.csv \
    --fiber-diameter 10 --n-nodes 51 \
    --f1 4000 --f2 4100 --amplitude1 1.0 --amplitude2 1.0 --tstop 50 --dt 0.001
```

This builds the femoral nerve fiber, assigns the two interpolated COMSOL potential fields as
the fiber's two stimulation sources (`fiber.potentials = [v1, v2]`), drives them with sinusoidal
waveforms at `f1`/`f2` via `pyfibers.ScaledStim`, and reports whether/when an action potential
was detected.
