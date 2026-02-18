# SMILES to 3D SDF Service

Lightweight FastAPI service that converts SMILES strings into 3D SDF files using RDKit. It also exposes a small info endpoint for basic molecular properties.

## Contents
- `main.py` - FastAPI application and conversion logic (ETKDGv3 embedding, MMFF94 optimisation with UFF fallback).
- `requirements.txt` - Python dependencies.
- `Dockerfile` - Docker image to run the service.

## Requirements
- Python 3.11
- RDKit (platform-dependent; see notes)
- FastAPI, Uvicorn, Pydantic (listed in `requirements.txt`)

Note: RDKit installation can be platform-specific. If `pip install rdkit` fails, prefer a conda environment (recommended):

```bash
conda create -n rdkit-env -c conda-forge python=3.11 rdkit fastapi uvicorn pydantic
conda activate rdkit-env
```

## Install (pip)

```bash
python -m venv venv
venv\Scripts\activate  # Windows
# or: source venv/bin/activate  # Linux / macOS
pip install -r requirements.txt
```

## Run locally

Start the app with Uvicorn:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

The service will be available at http://localhost:8000.

## Docker

Build and run the container:

```bash
docker build -t rdkitapi .
docker run --rm -p 8000:8000 rdkitapi
```

If the Docker build fails due to RDKit wheel availability, use a conda-based image or an official RDKit container as a base.

## API

- GET `/health`
  - Returns: `{ "status": "ok" }`

- GET `/convert?smiles=<SMILES>`
  - Returns: a 3D SDF file (`chemical/x-mdl-sdfile`) as an attachment (`molecule.sdf`).
  - Example: `GET /convert?smiles=CCO`

- POST `/convert` (JSON body)
  - Body: `{ "smiles": "CCO" }`
  - Returns: a 3D SDF file as above.

- GET `/info?smiles=<SMILES>`
  - Returns JSON with basic properties:
    - `smiles` (string)
    - `molecular_formula` (string)
    - `molecular_weight` (float)
    - `num_atoms` (int)
    - `num_heavy_atoms` (int)

## Examples

Download an SDF with curl (GET):

```bash
curl -sS "http://localhost:8000/convert?smiles=CCO" -o molecule.sdf
```

Download an SDF with curl (POST):

```bash
curl -sS -X POST "http://localhost:8000/convert" -H "Content-Type: application/json" -d "{\"smiles\":\"CCO\"}" -o molecule.sdf
```

Get molecule info:

```bash
curl -sS "http://localhost:8000/info?smiles=CCO"
```

## Implementation notes

- main.py uses RDKit's ETKDGv3 (seeded with `randomSeed = 42`) to generate 3D coordinates and MMFF94 for geometry optimisation; if MMFF fails it falls back to UFF.
- The service adds explicit hydrogens before embedding and writes SDF (V2000) output.
- Invalid SMILES or failures to embed/optimise return HTTP 400 with an explanatory message.

## Files
- `main.py` - application and conversion code
- `requirements.txt` - pinned dependencies
- `Dockerfile` - simple image using `python:3.11-slim`

## Notes / Troubleshooting
- RDKit wheels are often large and platform-specific; using conda (conda-forge) is the most reliable way to get RDKit working across platforms.
- If you need persistent changes to generation (seed, optimizer settings), edit `smiles_to_3d_sdf` in `main.py`.

---

No license specified.
