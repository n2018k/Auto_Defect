# ==============================================================================
# FILE: prefactor_step.py
#
# Contains the logic for calculating the diffusion prefactor from vibrational frequencies.
# ==============================================================================
import os
import numpy as np
from ase.io import read
from ase.vibrations import Vibrations
from mattersim.forcefield.potential import MatterSimCalculator

def get_frequencies_as_reals(atoms_path: str, vib_dir_name: str, device: str, summary_file_path: str, model_path="MatterSim-v1.0.0-5M.pth"):
    """
    Calculates and returns the vibrational frequencies as a list of real numbers,
    and saves the summary to a file.
    """
    print(f"    > Calculating frequencies for {os.path.basename(atoms_path)}...")
    atoms = read(atoms_path)
    atoms.calc = MatterSimCalculator(load_path=model_path, device=device)
    
    vib = Vibrations(atoms, name=vib_dir_name)
    vib.run()
    
    # Write the summary to the specified file
    with open(summary_file_path, 'w') as f:
        vib.summary(log=f)
    print(f"    > Vibration summary saved to {os.path.basename(summary_file_path)}")
    
    complex_frequencies = vib.get_frequencies().tolist()
    real_frequencies = [c.real for c in complex_frequencies]
    
    return real_frequencies

def calculate_prefactor(initial_state_path: str, saddle_state_path: str, directory: str, device: str):
    """
    Calculates the diffusion prefactor using the Vineyard formalism.
    Returns the prefactor in THz if successful, None otherwise.
    """
    print("  > Calculating diffusion prefactor...")
    
    try:
        initial_vib_dir = os.path.join(directory, 'vib_initial')
        saddle_vib_dir = os.path.join(directory, 'vib_saddle')
        
        # Define paths for the summary files
        initial_summary_path = os.path.join(directory, 'initial_vib.dat')
        saddle_summary_path = os.path.join(directory, 'saddle_vib.dat')
        
        initial_freqs = get_frequencies_as_reals(initial_state_path, initial_vib_dir, device=device, summary_file_path=initial_summary_path)
        saddle_freqs = get_frequencies_as_reals(saddle_state_path, saddle_vib_dir, device=device, summary_file_path=saddle_summary_path)
        
        print(f"    > Found {len(initial_freqs)} frequencies for the initial state.")
        print(f"    > Found {len(saddle_freqs)} frequencies for the saddle state.")

        print("    > USER WARNING: For trustworthy results, please visually inspect the *.dat files")
        print("    > and confirm the initial state has 3 imaginary/zero modes and the")
        print("    > saddle state has exactly one additional imaginary mode.")

        prefactor_cm = initial_freqs[3]
        for i, s in zip(initial_freqs[4:], saddle_freqs[4:]):
            prefactor_cm *= i / s
            
        prefactor_thz = prefactor_cm * 0.0299792458
        
        print(f"  > Calculated prefactor: {prefactor_thz:.4f} THz")
        return prefactor_thz

    except Exception as e:
        print(f"An error occurred during prefactor calculation: {e}")
        return None
