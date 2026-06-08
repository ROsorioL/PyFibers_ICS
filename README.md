# PyFibers ICS — Femoral Nerve Interferential Current Stimulation

Simulation of a femoral nerve fiber model in [PyFibers](https://pyfibers.readthedocs.io/), driven by
extracellular potentials generated from an interferential current stimulation (IFC) field model in COMSOL.

## Pipeline

1. **COMSOL**: Build the IFC field model of the femoral nerve region and export the extracellular
   potential distribution (e.g., as CSV/TXT) to [comsol_exports/](comsol_exports/).
2. **Loader**: [src/load_comsol_potentials.py](src/load_comsol_potentials.py) reads the exported field
   and interpolates potentials onto fiber spatial coordinates.
3. **PyFibers**: [src/run_simulation.py](src/run_simulation.py) builds the femoral nerve fiber model,
   applies the interpolated extracellular potentials as the stimulus, and runs the simulation.
4. **Results**: Outputs (membrane voltages, activation thresholds, plots) are written to [results/](results/).

## Project layout

```
comsol_exports/   Raw COMSOL field exports (potentials vs. spatial coordinates)
src/              Python source: COMSOL loader + PyFibers simulation scripts
notebooks/        Exploratory analysis / visualization notebooks
results/          Simulation outputs and figures
docs/             Notes on the COMSOL model setup and simulation parameters
```

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate   # Windows
pip install -r requirements.txt
```

## Usage

```bash
python src/run_simulation.py --comsol-file comsol_exports/<your_export>.csv
```
