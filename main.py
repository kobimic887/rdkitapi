from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import Response
from pydantic import BaseModel
from rdkit import Chem
from rdkit.Chem import AllChem, Descriptors, rdMolDescriptors
import io

app = FastAPI(
    title="SMILES to 3D SDF Service",
    description="Convert SMILES strings to 3D SDF files using RDKit",
    version="1.0.0",
)


class SmilesRequest(BaseModel):
    smiles: str


class MoleculeInfo(BaseModel):
    smiles: str
    molecular_formula: str
    molecular_weight: float
    num_atoms: int
    num_heavy_atoms: int


def smiles_to_3d_sdf(smiles: str) -> str:
    """Convert a SMILES string to a 3D SDF block.

    Pipeline:
    1. Parse SMILES into an RDKit molecule.
    2. Add explicit hydrogens.
    3. Generate a 3D conformer with ETKDG.
    4. Optimise geometry with the MMFF94 force-field.
    5. Write out as an SDF block (V2000).
    """
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        raise ValueError(f"Invalid SMILES string: {smiles}")

    # Add hydrogens for realistic 3D geometry
    mol = Chem.AddHs(mol)

    # Generate 3D coordinates using ETKDG (distance-geometry + knowledge-based)
    params = AllChem.ETKDGv3()
    params.randomSeed = 42
    result = AllChem.EmbedMolecule(mol, params)
    if result == -1:
        raise ValueError(
            f"Could not generate 3D coordinates for SMILES: {smiles}"
        )

    # Optimise with MMFF94 force field
    optimise_result = AllChem.MMFFOptimizeMolecule(mol, maxIters=2000)
    if optimise_result == -1:
        # MMFF failed – fall back to UFF
        AllChem.UFFOptimizeMolecule(mol, maxIters=2000)

    # Write SDF block
    writer = Chem.SDWriter(sdf_buffer := io.StringIO())
    writer.write(mol)
    writer.close()
    return sdf_buffer.getvalue()


# ── Endpoints ────────────────────────────────────────────────────────────────


@app.get("/health")
def health_check():
    """Health-check endpoint."""
    return {"status": "ok"}


@app.get(
    "/convert",
    response_class=Response,
    summary="Convert SMILES to 3D SDF (GET)",
    responses={
        200: {
            "content": {"chemical/x-mdl-sdfile": {}},
            "description": "3D SDF file",
        }
    },
)
def convert_smiles_get(
    smiles: str = Query(..., description="SMILES string to convert"),
):
    """Accept a SMILES string as a query parameter and return a 3D SDF file."""
    try:
        sdf_content = smiles_to_3d_sdf(smiles)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return Response(
        content=sdf_content,
        media_type="chemical/x-mdl-sdfile",
        headers={
            "Content-Disposition": "attachment; filename=molecule.sdf"
        },
    )


@app.post(
    "/convert",
    response_class=Response,
    summary="Convert SMILES to 3D SDF (POST)",
    responses={
        200: {
            "content": {"chemical/x-mdl-sdfile": {}},
            "description": "3D SDF file",
        }
    },
)
def convert_smiles_post(body: SmilesRequest):
    """Accept a SMILES string in the request body and return a 3D SDF file."""
    try:
        sdf_content = smiles_to_3d_sdf(body.smiles)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return Response(
        content=sdf_content,
        media_type="chemical/x-mdl-sdfile",
        headers={
            "Content-Disposition": "attachment; filename=molecule.sdf"
        },
    )


@app.post(
    "/convertSTR",
    summary="Convert SMILES to 3D SDF string (POST)",
)
def convert_str_smiles_post(body: SmilesRequest):
    """Accept a SMILES string and return the 3D SDF content as a string."""
    try:
        sdf_content = smiles_to_3d_sdf(body.smiles)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return {"sdf": sdf_content}


@app.get(
    "/info",
    response_model=MoleculeInfo,
    summary="Get molecule info from SMILES",
)
def molecule_info(
    smiles: str = Query(..., description="SMILES string"),
):
    """Return basic molecular properties for a given SMILES string."""
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        raise HTTPException(
            status_code=400, detail=f"Invalid SMILES string: {smiles}"
        )

    return MoleculeInfo(
        smiles=smiles,
        molecular_formula=rdMolDescriptors.CalcMolFormula(mol),
        molecular_weight=round(Descriptors.MolWt(mol), 4),
        num_atoms=mol.GetNumAtoms(onlyExplicit=False),
        num_heavy_atoms=mol.GetNumHeavyAtoms(),
    )
