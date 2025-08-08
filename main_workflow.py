# ==============================================================================
# FILE: main_workflow.py
#
# This is the main script you will run from the command line.
# It controls the entire workflow.
#
# USAGE:
# python main_workflow.py your_structure_file.cif
# ==============================================================================
import sys
import os
import torch
from pymatgen.io.ase import AseAtomsAdaptor

# Import the functions from our other modules
from relaxer_step import run_bulk_relaxation
from supercell_step import create_supercell
from pathfinder_step import find_unique_hops
from io_step import manage_path_calculations

# --- Main Workflow Configuration ---
MIGRATING_ELEMENT = "Li"
MAX_HOP_DISTANCE = 7.0 
MIN_SUPERCELL_LENGTH = 10.0
MAX_SUPERCELL_ATOMS = 1000
DISTANCE_PRECISION = 2
NUM_NEB_IMAGES = 3 # Number of intermediate images for the NEB calculation
NEB_MAX_STEPS = 5000 # Maximum number of steps for NEB optimization

def main():
    """
    Orchestrates the entire pipeline from relaxation to NEB file generation.
    """
    # --- Device Configuration ---
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"--- Using device: {device.upper()} ---")

    # 1. Get input file from command line
    if len(sys.argv) < 2:
        print("Usage: python main_workflow.py <path_to_structure_file>")
        sys.exit(1)
    input_filename = sys.argv[1]

    if not os.path.exists(input_filename):
        print(f"Error: The input file '{input_filename}' was not found.")
        sys.exit(1)

    # --- Step 1: Relax initial (primitive) structure ---
    print("--- Step 1: Relaxing initial structure with MatterSim ---")
    relaxed_ase_atoms = run_bulk_relaxation(input_filename, device=device)
    if relaxed_ase_atoms is None:
        print("Initial relaxation failed. Exiting.")
        sys.exit(1)
    print("Initial relaxation complete.\n")
    
    # Convert the relaxed ASE Atoms object to a Pymatgen Structure object
    initial_pmg_structure = AseAtomsAdaptor.get_structure(relaxed_ase_atoms)

    # --- Step 2: Create Supercell ---
    print("--- Step 2: Creating supercell from relaxed primitive cell ---")
    unrelaxed_supercell = create_supercell(
        initial_pmg_structure,
        min_length=MIN_SUPERCELL_LENGTH,
        max_atoms=MAX_SUPERCELL_ATOMS
    )
    # Save the unrelaxed supercell to a temporary file for the next relaxation step
    temp_supercell_filename = "POSCAR_supercell_unrelaxed"
    unrelaxed_supercell.to(fmt="poscar", filename=temp_supercell_filename)
    print("Supercell creation complete.\n")

    # --- Step 3: Relax the Supercell ---
    print("--- Step 3: Relaxing the supercell with MatterSim ---")
    relaxed_supercell_ase = run_bulk_relaxation(temp_supercell_filename, device=device)
    if relaxed_supercell_ase is None:
        print("Supercell relaxation failed. Exiting.")
        os.remove(temp_supercell_filename) # Clean up temp file
        sys.exit(1)
    
    # Convert the final relaxed supercell back to a pymatgen object
    pristine_supercell = AseAtomsAdaptor.get_structure(relaxed_supercell_ase)
    print("Supercell relaxation complete.\n")
    
    # Clean up the temporary file
    os.remove(temp_supercell_filename)

    # Write the FINAL relaxed supercell to a file for reference
    from io_step import write_supercell_file
    write_supercell_file(pristine_supercell)
    
    # --- Step 4: Find Migration Paths ---
    print("--- Step 4: Finding unique migration paths in relaxed supercell ---")
    final_hops_to_generate = find_unique_hops(
        pristine_supercell,
        migrating_element=MIGRATING_ELEMENT,
        max_hop_distance=MAX_HOP_DISTANCE,
        distance_precision=DISTANCE_PRECISION
    )
    if not final_hops_to_generate:
        print("Could not find any migration paths. Exiting.")
        sys.exit(1)
    print(f"Found {len(final_hops_to_generate)} symmetrically unique migration hops to investigate.\n")

    # --- Step 5: Manage calculations for each path (with restart capability) ---
    print("--- Step 5: Managing calculations for each migration path ---")
    for i, hop in enumerate(final_hops_to_generate):
        site1_idx, site2_idx = hop
        manage_path_calculations(
            pristine_supercell, site1_idx, site2_idx, i + 1, NUM_NEB_IMAGES, NEB_MAX_STEPS, device=device
        )
    print("\nAll path calculations managed.")

    print("Workflow finished successfully!")


if __name__ == "__main__":
    main()
