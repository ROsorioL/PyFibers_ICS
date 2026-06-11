# Tutorial: Femoral Nerve IFC Simulation with PyFibers + COMSOL

This tutorial walks you through using this project end-to-end: from a COMSOL field
export, to a running PyFibers/NEURON simulation of a femoral nerve fiber under
interferential current (IFC) stimulation, to interpreting the results.

---

## 1. What you'll build

A pipeline that answers: *"For a given femoral nerve fiber, and a given IFC electrode
configuration (two channels at slightly different carrier frequencies), does the fiber
fire an action potential — and when?"*

```
COMSOL (2 unit-current field exports)
        │
        ▼
load_comsol_potentials.py  →  interpolate fields onto fiber coordinates
        │
        ▼
run_simulation.py  →  build fiber, apply IFC waveforms, run NEURON
        │
        ▼
"Action potential detected: True/False, at t = ... ms"
```

---

## 2. One-time environment setup (WSL)

NEURON (PyFibers' simulation engine) has no Windows pip wheels, so we use WSL Ubuntu.

```bash
# In Windows PowerShell (as admin), one-time:
wsl --install
# reboot if prompted, then open Ubuntu

# Inside Ubuntu:
sudo apt-get update
sudo apt-get install -y python3-venv python3-pip build-essential

python3 -m venv ~/pyfibers_env
source ~/pyfibers_env/bin/activate
pip install pyfibers numpy scipy pandas matplotlib neuron

# Compile the NEURON mechanism files bundled with PyFibers (one-time):
python -c "import pyfibers; print(pyfibers.MOD_dir)"
cd <path printed above>
nrnivmodl
```

Verify it worked:

```bash
python -c "import neuron, pyfibers; print(neuron.__version__, 'pyfibers ok')"
# -> 9.0.1 pyfibers ok
```

> Tip: your project folder on the Windows side (e.g.
> `C:\Users\you\...\PyFibers_ICS`) is reachable from WSL at
> `/mnt/c/Users/you/.../PyFibers_ICS`.

---

## 3. Step 1 — Get your COMSOL field exports

You need **two** files, one per IFC electrode-pair channel, each containing the
**potential per unit injected current** (a "lead field"). See
[documentation.pdf](documentation.pdf) §6 / the project README for the full COMSOL
recipe; in short, for each channel:

1. Build the femoral nerve tissue geometry with realistic conductivities.
2. Set one electrode pair as `Terminal` (current = 1 A) and `Ground`.
3. Run a **stationary** study (`Electric Currents` physics — quasi-static is fine for
   IFC frequencies).
4. Export `x, y, z, V` (µm, V) over the region your fiber passes through.

Save the two files as, e.g.:

```
comsol_exports/channel1_field.csv
comsol_exports/channel2_field.csv
```

Each row should look like:

```
1023.4, -540.2, 12500.0, 0.000182
```

(`x, y, z` in µm, `V` in volts per 1 A injected).

> **Don't have COMSOL data yet?** You can still test the pipeline with a synthetic
> point-source field — see §7 (Smoke test).

---

## 4. Step 2 — Understand the fiber model

The pipeline builds a **femoral nerve fiber** using PyFibers' MRG (McIntyre–Richardson–
Grill) double-cable model — a standard model for large myelinated peripheral axons.

Key parameters you'll choose:

| Parameter | Meaning | Typical femoral nerve values |
|---|---|---|
| `--fiber-diameter` | Axon diameter (µm) | 8–16 µm for large motor/sensory fibers |
| `--n-nodes` | Number of nodes of Ranvier | More nodes = longer fiber; 51 is a reasonable default |
| `--fiber-model` | PyFibers `FiberModel` | `MRG_INTERPOLATION` (default) for myelinated fibers |

The fiber is placed along the z-axis starting at the origin by default. **Your COMSOL
coordinates must use the same frame** (or you should translate/rotate the fiber via
`fiber.set_xyz(...)` to match the COMSOL geometry — see §8 for customization).

---

## 5. Step 3 — Understand the IFC stimulus

Two channels, each a sinusoidal current at a slightly different frequency:

| Parameter | Meaning | Typical IFC values |
|---|---|---|
| `--f1`, `--f2` | Channel carrier frequencies (Hz) | e.g. 4000, 4100 |
| `--amplitude1`, `--amplitude2` | Scale factors applied to each channel's unit-current field | depends on your COMSOL normalization (see §6 of the requirements doc) |
| `--tstop` | Total simulated time (ms) | enough to cover several beat cycles, e.g. 50 ms |
| `--dt` | NEURON integration time step (ms) | 0.001–0.005 ms |

The **beat frequency** (`|f2 - f1|`, e.g. 100 Hz) is computed automatically and printed —
this is the low-frequency envelope that emerges where the two fields overlap.

---

## 6. Step 4 — Run the simulation

From the project root (in WSL, with the venv activated):

```bash
source ~/pyfibers_env/bin/activate
cd /mnt/c/Users/<you>/.../PyFibers_ICS

python src/run_simulation.py \
    --channel1-file comsol_exports/channel1_field.csv \
    --channel2-file comsol_exports/channel2_field.csv \
    --fiber-diameter 10 --n-nodes 51 \
    --f1 4000 --f2 4100 \
    --amplitude1 1.0 --amplitude2 1.0 \
    --tstop 50 --dt 0.001
```

### Expected output

```
Built fiber: MRG_INTERPOLATION, 221 coordinates
Beat frequency at target tissue: 100.0 Hz
Action potential detected: True (count=1.0), at t = 1.25 ms
```

- **`Built fiber: ... N coordinates`** — confirms the fiber model was constructed; `N`
  depends on `--n-nodes` and the model's internal segmentation.
- **`Beat frequency`** — sanity check that your `f1`/`f2` give the IFC envelope you
  intended.
- **`Action potential detected`** — `True`/`False` and, if `True`, the time (ms) the AP
  was detected at the recording location (default 90% along the fiber).

---

## 7. Smoke test (no COMSOL data needed)

To confirm your environment works before you have real COMSOL exports, generate a
synthetic point-source field:

```bash
python - <<'EOF'
import numpy as np
xs = np.linspace(-2000, 2000, 9)
ys = np.linspace(-2000, 2000, 9)
zs = np.linspace(0, 50000, 50)
X, Y, Z = np.meshgrid(xs, ys, zs, indexing='ij')
pts = np.column_stack([X.ravel(), Y.ravel(), Z.ravel()])
for name, center in [('channel1_field.csv', np.array([1000, 0, 25000])),
                      ('channel2_field.csv', np.array([-1000, 0, 25000]))]:
    r = np.linalg.norm(pts - center, axis=1) + 1.0
    V = 1.0 / (4*np.pi*0.3*r)  # point-source potential per unit current
    np.savetxt(f'comsol_exports/{name}', np.column_stack([pts, V]), delimiter=',')
print("synthetic exports written")
EOF

python src/run_simulation.py \
    --channel1-file comsol_exports/channel1_field.csv \
    --channel2-file comsol_exports/channel2_field.csv \
    --fiber-diameter 10 --n-nodes 21 \
    --f1 4000 --f2 4100 --amplitude1 50 --amplitude2 50 \
    --tstop 10 --dt 0.005
```

If this prints `Built fiber: ...`, `Beat frequency: 100.0 Hz`, and an AP detection line
without errors, your environment is correctly set up.

---

## 8. Customizing the pipeline

### Sweeping stimulation amplitude (finding a threshold)

To find the minimum amplitude that triggers an AP, run the simulation in a loop with
increasing `--amplitude1`/`--amplitude2` (keeping their ratio fixed) until
`Action potential detected: True` appears. (PyFibers also has a built-in
`ScaledStim.find_threshold` helper — see the PyFibers docs — which could replace this
manual sweep in a future extension.)

### Different fiber models or sizes

Change `--fiber-model` to any `pyfibers.FiberModel` member (e.g. `MRG_DISCRETE`,
`SUNDT`, `RATTAY` for unmyelinated fibers) and adjust `--fiber-diameter` /
`--n-nodes` accordingly. Smaller-diameter / unmyelinated models will generally need
smaller `--dt`.

### Aligning fiber and COMSOL coordinate frames

If your COMSOL geometry doesn't place the femoral nerve fiber along the z-axis from
the origin, translate the fiber to match before assigning potentials:

```python
fiber.set_xyz(x=..., y=..., z=...)
v1, v2 = load_channel_potentials(..., fiber.coordinates)
```

(Add this call in `run_simulation.py` between fiber construction and potential
loading.)

### Three IFC channels / "premodulated" IFC

The pipeline currently supports exactly two channels (`fiber.potentials = [v1, v2]`,
two waveforms, two `stimamp`s). To add a third (e.g. for "interferential" current with
a premodulated channel, or a tripolar electrode setup), extend each list to three
elements and provide a third COMSOL export.

---

## 9. Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `ModuleNotFoundError: No module named 'neuron'` | Running outside the WSL venv | `source ~/pyfibers_env/bin/activate` |
| `ValueError: argument not a density mechanism name` | NEURON `.mod` mechanisms not compiled | Run `nrnivmodl` in `pyfibers`'s `MOD` directory (§2) |
| Interpolated potentials are all `NaN` / pipeline crashes | Fiber coordinates fall completely outside the COMSOL export's spatial range | Check units (µm vs m) and coordinate frame alignment between fiber and COMSOL |
| `Action potential detected: False` even at high amplitude | Amplitude too low for your COMSOL normalization, or fiber not near the field maxima | Increase `--amplitude1/2`, check `fiber.coordinates` lie within the high-field region of your COMSOL model |
| Beat frequency looks wrong | `--f1`/`--f2` swapped or equal | `beat_frequency = |f2 - f1|`; ensure they differ as intended |

---

## 10. Where to go next

- [`README.md`](../README.md) — quick reference / setup commands
- [`documentation.pdf`](documentation.pdf) — full requirements reference and
  line-by-line code walkthrough
- [PyFibers documentation](https://pyfibers.readthedocs.io/) — fiber models,
  `ScaledStim` options, threshold-finding utilities
