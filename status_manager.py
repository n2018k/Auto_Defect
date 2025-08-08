# ==============================================================================
# FILE: status_manager.py
#
# Contains functions for managing the status.json checkpoint file.
# ==============================================================================
import os
import json

STATUS_FILENAME = "status.json"

DEFAULT_STATUS = {
    "initial_relax_complete": False,
    "final_relax_complete": False,
    "neb_steps_taken": 0,
    "neb_climb_steps_taken": 0,
    "neb_analysis_complete": False,
    "prefactor_complete": False,
    "neb_barrier_eV": None,
    "prefactor_THz": None
}

def get_status(directory: str) -> dict:
    """
    Reads the status.json file from a directory. If it doesn't exist,
    it creates a default one.
    """
    status_path = os.path.join(directory, STATUS_FILENAME)
    
    if not os.path.exists(status_path):
        with open(status_path, 'w') as f:
            json.dump(DEFAULT_STATUS, f, indent=4)
        return DEFAULT_STATUS
    else:
        with open(status_path, 'r') as f:
            try:
                status = json.load(f)
                # Ensure all keys are present, in case the format changes
                for key, value in DEFAULT_STATUS.items():
                    if key not in status:
                        status[key] = value
                return status
            except json.JSONDecodeError:
                # If the file is corrupted, create a new default one
                print(f"Warning: Corrupted status file in {directory}. Resetting.")
                with open(status_path, 'w') as f:
                    json.dump(DEFAULT_STATUS, f, indent=4)
                return DEFAULT_STATUS

def update_status(directory: str, key_to_update: str, value):
    """
    Updates a specific key in the status.json file with a given value.
    """
    status = get_status(directory)
    status[key_to_update] = value
    
    status_path = os.path.join(directory, STATUS_FILENAME)
    with open(status_path, 'w') as f:
        json.dump(status, f, indent=4)
