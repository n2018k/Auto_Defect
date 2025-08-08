# ==============================================================================
# FILE: io_step.py
#
# Contains functions for writing all output files and managing the calculation state.
# ==============================================================================
import os
from pymatgen.core import Structure
from ase.io import write
from relaxer_step import run_vacancy_relaxation
from neb_step import run_neb_calculation
from status_manager import get_status, update_status

def write_supercell_file(structure: Structure):
    """Saves the pristine supercell structure to a POSCAR file."""
    supercell_filename = "POSCAR_supercell_pristine"
    structure.to(fmt="poscar", filename=supercell_filename)
    print(f"Pristine supercell structure saved to '{supercell_filename}'.\n")

def manage_path_calculations(pristine_structure: Structure, migrating_atom_idx: int, vacancy_idx: int, path_num: int, num_images: int, neb_max_steps: int, device: str):
    """
    Manages the entire calculation workflow for a single migration path,
    including checkpointing and restarting.
    """
    distance = pristine_structure.get_distance(migrating_atom_idx, vacancy_idx)
    dir_name = f"NEB_path_{path_num:03d}_({migrating_atom_idx}_to_{vacancy_idx})_dist_{distance:.2f}A"
    os.makedirs(dir_name, exist_ok=True)
    print(f"\n--- Managing Path: {dir_name} ---")

    # Get the current status of this path's calculations
    status = get_status(dir_name)

    # Define all file paths for this directory
    initial_poscar_path = os.path.join(dir_name, "POSCAR_initial")
    final_poscar_path = os.path.join(dir_name, "POSCAR_final")
    initial_traj_path = os.path.join(dir_name, "initial.traj")
    final_traj_path = os.path.join(dir_name, "final.traj")
    optimized_initial_path = os.path.join(dir_name, "POSCAR_optimized_initial")
    optimized_final_path = os.path.join(dir_name, "POSCAR_optimized_final")
    
    # --- Step 1: Create initial/final unrelaxed structures (if they don't exist) ---
    if not os.path.exists(initial_poscar_path):
        print("  > Creating initial unrelaxed structure...")
        initial_structure = pristine_structure.copy()
        initial_structure.remove_sites([vacancy_idx])
        initial_structure.to(fmt="poscar", filename=initial_poscar_path)
    
    if not os.path.exists(final_poscar_path):
        print("  > Creating final unrelaxed structure...")
        final_structure = pristine_structure.copy()
        final_structure.remove_sites([vacancy_idx])
        if migrating_atom_idx > vacancy_idx:
            migrating_atom_new_idx = migrating_atom_idx - 1
        else:
            migrating_atom_new_idx = migrating_atom_idx
        destination_coords = pristine_structure[vacancy_idx].frac_coords
        final_structure[migrating_atom_new_idx].frac_coords = destination_coords
        final_structure.to(fmt="poscar", filename=final_poscar_path)

    # --- Step 2: Relax initial endpoint ---
    if not status["initial_relax_complete"]:
        relaxed_initial = run_vacancy_relaxation(initial_poscar_path, initial_traj_path, device=device)
        if relaxed_initial:
            write(optimized_initial_path, relaxed_initial, direct=True, format='vasp')
            print(f"  > Saved final relaxed structure to {os.path.basename(optimized_initial_path)}")
            update_status(dir_name, "initial_relax_complete", True)
    else:
        print("  > Skipping initial relaxation (already complete).")

    # --- Step 3: Relax final endpoint ---
    if not status["final_relax_complete"]:
        relaxed_final = run_vacancy_relaxation(final_poscar_path, final_traj_path, device=device)
        if relaxed_final:
            write(optimized_final_path, relaxed_final, direct=True, format='vasp')
            print(f"  > Saved final relaxed structure to {os.path.basename(optimized_final_path)}")
            update_status(dir_name, "final_relax_complete", True)
    else:
        print("  > Skipping final relaxation (already complete).")

    # --- Step 4: Run NEB Calculation and Analysis ---
    # Only run if both endpoints are successfully relaxed
    if get_status(dir_name)["initial_relax_complete"] and get_status(dir_name)["final_relax_complete"]:
        if status["neb_steps_taken"] == 0 or status["neb_climb_steps_taken"] == 0:
            results = run_neb_calculation(
                initial_path=initial_traj_path,
                final_path=final_traj_path,
                optimized_initial_path=optimized_initial_path,
                directory=dir_name,
                num_images=num_images,
                max_steps=neb_max_steps,
                device=device
            )
            # Update status based on the detailed results dictionary
            update_status(dir_name, "neb_steps_taken", results["neb_steps"])
            update_status(dir_name, "neb_climb_steps_taken", results["climb_steps"])
            if results["analysis_ok"]:
                update_status(dir_name, "neb_analysis_complete", True)
                update_status(dir_name, "neb_barrier_eV", results["barrier_eV"])
            if results["prefactor_ok"]:
                update_status(dir_name, "prefactor_complete", True)
                update_status(dir_name, "prefactor_THz", results["prefactor_THz"])
        else:
            print(f"  > Skipping NEB calculation (already run).")
    else:
        print("  > Skipping NEB calculation (endpoints not ready).")
