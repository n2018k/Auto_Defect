# ==============================================================================
# FILE: neb_step.py
#
# Contains the logic for setting up and running the NEB calculation.
# ==============================================================================
import os
import numpy as np
from ase.io import read, write
from ase.mep.neb import NEB, NEBTools
from ase.optimize import LBFGS, FIRE
from ase.utils.forcecurve import fit_images # New import
from mattersim.forcefield.potential import MatterSimCalculator
from prefactor_step import calculate_prefactor # Import the new prefactor function

def run_neb_calculation(initial_path: str, final_path: str, optimized_initial_path: str, directory: str, num_images: int, max_steps: int, device: str, model_path="MatterSim-v1.0.0-5M.pth"):
    """
    Sets up and runs a two-stage (standard then climbing) NEB calculation.
    Returns a dictionary with the status and results of each stage.
    """
    results = {
        "neb_converged": False, "climb_converged": False,
        "analysis_ok": False, "prefactor_ok": False,
        "neb_steps": 0, "climb_steps": 0,
        "barrier_eV": None, "prefactor_THz": None
    }
    
    try:
        # --- Stage 1: Standard NEB with multiple attempts ---
        print(f"  > Setting up Standard NEB in '{directory}'...")
        initial = read(initial_path)
        final = read(final_path)

        optimizers_to_try = [
            {'optimizer': FIRE, 'method': 'improvedtangent', 'fmax': 0.01},
            {'optimizer': FIRE, 'method': 'aseneb', 'fmax': 0.01},
            {'optimizer': LBFGS, 'method': 'improvedtangent', 'fmax': 0.01},
            {'optimizer': LBFGS, 'method': 'aseneb', 'fmax': 0.01},
        ]

        standard_neb_converged = False
        neb_traj_path = os.path.join(directory, 'neb.traj')

        for i, params in enumerate(optimizers_to_try):
            print(f"    > Attempt {i+1}/4: Using {params['optimizer'].__name__} with method '{params['method']}'...")
            
            # Create a fresh list of images for this attempt
            attempt_images = [initial.copy()]
            for _ in range(num_images):
                attempt_images.append(initial.copy())
            attempt_images.append(final.copy())
            
            # Attach calculators to ALL images, including endpoints
            for img in attempt_images:
                img.calc = MatterSimCalculator(load_path=model_path, device=device)
            
            neb = NEB(attempt_images, allow_shared_calculator=False, method=params['method'])
            neb.interpolate(mic=True)

            optimizer = params['optimizer'](neb, trajectory=neb_traj_path)

            converged_this_attempt = optimizer.run(fmax=params['fmax'], steps=max_steps)
            
            if converged_this_attempt:
                print(f"    > Standard NEB converged in {optimizer.nsteps} steps.")
                standard_neb_converged = True
                results["neb_steps"] = optimizer.nsteps
                break
            else:
                print(f"    > Did not converge with this method.")
        
        if not standard_neb_converged:
            print(f"  > WARNING: Standard NEB did not converge with any method within {max_steps} steps.")
            results["neb_steps"] = max_steps
            return results

        # --- Stage 2: Climbing Image NEB ---
        print(f"  > Setting up Climbing Image NEB in '{directory}'...")
        total_images = num_images + 2
        climb_images_initial = read(neb_traj_path + f'@-{total_images}:')
        
        climb_optimizers_to_try = [
            {'optimizer': FIRE, 'method': 'improvedtangent', 'fmax': 0.001},
            {'optimizer': FIRE, 'method': 'aseneb', 'fmax': 0.001},
            {'optimizer': LBFGS, 'method': 'improvedtangent', 'fmax': 0.001},
            {'optimizer': LBFGS, 'method': 'aseneb', 'fmax': 0.001},
        ]

        climb_neb_converged = False
        climb_traj_path = os.path.join(directory, 'neb_climb.traj')

        for i, params in enumerate(climb_optimizers_to_try):
            print(f"    > Climb Attempt {i+1}/4: Using {params['optimizer'].__name__} with method '{params['method']}'...")

            climb_images = [img.copy() for img in climb_images_initial]
            # Attach calculators to ALL images for the climb
            for img in climb_images:
                img.calc = MatterSimCalculator(load_path=model_path, device=device)

            climb_neb = NEB(climb_images, climb=True, allow_shared_calculator=False, method=params['method'])
            
            climb_optimizer = params['optimizer'](climb_neb, trajectory=climb_traj_path)

            converged_this_attempt = climb_optimizer.run(fmax=params['fmax'], steps=max_steps)
            
            if converged_this_attempt:
                print(f"    > Climbing Image NEB converged in {climb_optimizer.nsteps} steps.")
                climb_neb_converged = True
                results["climb_steps"] = climb_optimizer.nsteps
                break
            else:
                print(f"    > Did not converge with this method.")

        if not climb_neb_converged:
            print(f"  > WARNING: Climbing Image NEB did not converge within {max_steps} steps.")
            results["climb_steps"] = max_steps
            return results
        
        # --- Post-processing (using climb results) ---
        print("  > Post-processing CI-NEB results...")
        
        converged_climb_images = read(climb_traj_path + f'@-{total_images}:')
        neb_tools = NEBTools(converged_climb_images)
        
        barrier, dE = neb_tools.get_barrier()
        results["barrier_eV"] = round(barrier, 4)
        print(f"  > Calculated CI-NEB barrier: {results['barrier_eV']} eV")
        
        # Use fit_images to get the energies
        forcefit = fit_images(converged_climb_images)
        lines = forcefit.lines
        energies = []
        for line in lines:
            energies.append(list(line[1])[1])
        print("  > Relative Energy of All Images: ", energies)

        saddle_index = np.argmax(energies)
        saddle_point = converged_climb_images[saddle_index]
        
        saddle_path = os.path.join(directory, 'POSCAR_saddle')
        write(saddle_path, saddle_point, format='vasp', direct=True)
        print(f"  > Saddle point (image {saddle_index}) structure written to {os.path.basename(saddle_path)}")
        results["analysis_ok"] = True

        # --- Prefactor Calculation ---
        prefactor_thz = calculate_prefactor(
            initial_state_path=optimized_initial_path,
            saddle_state_path=saddle_path,
            directory=directory,
            device=device
        )
        if prefactor_thz is not None:
            results["prefactor_THz"] = round(prefactor_thz, 4)
            results["prefactor_ok"] = True
        
        return results

    except Exception as e:
        print(f"An error occurred during the NEB calculation or post-processing in {directory}: {e}")
        return results
