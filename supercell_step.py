# ==============================================================================
# FILE: supercell_step.py
#
# Contains the logic for generating an appropriate supercell.
# ==============================================================================
from pymatgen.core import Structure
from pymatgen.analysis.defects.supercells import get_sc_fromstruct

def create_supercell(structure: Structure, min_length: float, max_atoms: int) -> Structure:
    """
    Determines and creates an optimal supercell for defect calculations.
    """
    print(f"Determining supercell matrix for min length {min_length} Å and max {max_atoms} atoms...")
    sc_matrix = get_sc_fromstruct(
        structure,
        min_length=min_length,
        max_atoms=max_atoms
    )
    
    supercell = structure.copy()
    supercell.make_supercell(sc_matrix)
    
    print("Supercell created.")
    print(f"Transformation matrix:\n{sc_matrix}")
    print(f"Supercell formula: {supercell.composition.reduced_formula}")
    print(f"Supercell number of atoms: {supercell.num_sites}")
    
    return supercell
