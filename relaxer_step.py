# ==============================================================================
# FILE: relaxer_step.py
#
# Contains the logic for relaxing a structure using MatterSim.
# ==============================================================================
# Make sure you have the required libraries installed:
# pip install ase mattersim torch
import os
import numpy as np
from ase.io import read, write
from mattersim.forcefield.potential import MatterSimCalculator
from mattersim.applications.relax import Relaxer

def run_bulk_relaxation(filename, device, model_path="MatterSim-v1.0.0-5M.pth"):
    """
    Relaxes a structure, including the lattice vectors (bulk relaxation).
    """
    try:
        structure = read(filename)
        structure.calc = MatterSimCalculator(load_path=model_path, device=device)
        
        relaxer = Relaxer(
            optimizer="BFGS",
            filter="FrechetCellFilter", # Allows cell vectors to change
            constrain_symmetry=False,
        )
        
        relaxed_result = relaxer.relax(structure, steps=500, fmax=0.001)
        
        converged, relaxed_atoms = relaxed_result
        if converged:
            print(f"Bulk relaxation converged for {filename}.")
            return relaxed_atoms
        else:
            print(f"Warning: Bulk relaxation did not converge for {filename}.")
            return relaxed_atoms

    except Exception as e:
        print(f"An error occurred during bulk relaxation of {filename}: {e}")
        return None

def run_vacancy_relaxation(filename, trajectory_file, device, model_path="MatterSim-v1.0.0-5M.pth"):
    """
    Relaxes atomic positions only (fixed cell), for vacancy structures.
    This function now returns the relaxed atoms object.
    """
    try:
        print(f"  > Starting fixed-cell relaxation for {os.path.basename(filename)}...")
        structure = read(filename)
        structure.calc = MatterSimCalculator(load_path=model_path, device=device)
        
        relaxer = Relaxer(
            optimizer="BFGS", 
            filter=None, 
            constrain_symmetry=False
        )
        
        relaxed_result = relaxer.relax(
            structure, 
            steps=500, 
            fmax=0.001,
            trajectory=trajectory_file
        )
        
        converged, relaxed_atoms = relaxed_result
        if converged:
            print(f"  > Fixed-cell relaxation converged. Trajectory saved to {trajectory_file}")
            return relaxed_atoms
        else:
            print(f"  > Warning: Fixed-cell relaxation did not converge. Trajectory saved to {trajectory_file}")
            return None # Return None on failure to converge

    except Exception as e:
        print(f"An error occurred during vacancy relaxation of {filename}: {e}")
        return None
