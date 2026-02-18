Everything is working. Here's a summary of what was built:
---
SMILES to 3D SDF Service
Files created
| File | Purpose |
|---|---|
| main.py | FastAPI application with conversion logic |
| requirements.txt | Python dependencies |
| Dockerfile | Container image definition |
| .dockerignore | Docker build exclusions |
Endpoints
| Method | Path | Description |
|---|---|---|
| GET | /health | Health check |
| GET | /convert?smiles=CCO | Convert SMILES to 3D SDF via query param |
| POST | /convert | Convert SMILES to 3D SDF via JSON body {"smiles": "CCO"} |
| GET | /info?smiles=CCO | Get molecular properties (formula, weight, atom counts) |
3D conversion pipeline (main.py:27-63)
1. Parse SMILES into RDKit molecule
2. Add explicit hydrogens
3. Generate 3D conformer using ETKDGv3 (distance-geometry + knowledge-based)
4. Optimize geometry with MMFF94 force field (falls back to UFF if MMFF fails)
5. Write V2000 SDF block
Running locally
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
Running with Docker
docker build -t rdkitservice .
docker run -p 8000:8000 rdkitservice
Example usage
# GET request
curl "http://localhost:8000/convert?smiles=CCO" -o ethanol.sdf
# POST request
curl -X POST http://localhost:8000/convert \
  -H "Content-Type: application/json" \
  -d '{"smiles": "c1ccccc1"}' -o benzene.sdf
Interactive API docs are available at http://localhost:8000/docs.