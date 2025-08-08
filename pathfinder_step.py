# ==============================================================================
# FILE: pathfinder_step.py
#
# Contains the logic for finding all unique migration paths.
# ==============================================================================
from pymatgen.core import Structure
from pymatgen.symmetry.analyzer import SpacegroupAnalyzer

def find_unique_hops(structure: Structure, migrating_element: str, max_hop_distance: float, distance_precision: int) -> list:
    """
    Finds all symmetrically unique migration hops in a structure.
    """
    sga = SpacegroupAnalyzer(structure)
    symm_data = sga.get_symmetry_dataset()
    equivalent_atoms = symm_data["equivalent_atoms"]
    
    all_migrating_ion_indices = [
        i for i, site in enumerate(structure)
        if site.specie.symbol == migrating_element
    ]

    if not all_migrating_ion_indices:
        print(f"Error: No atoms of '{migrating_element}' found in the supercell.")
        return []

    processed_hop_types = set()
    final_hops_to_generate = []
    
    for start_idx in all_migrating_ion_indices:
        neighbors = structure.get_neighbors(structure[start_idx], max_hop_distance)
        
        for neighbor in neighbors:
            neighbor_dict = neighbor.as_dict()
            distance = neighbor_dict['nn_distance']
            end_idx = neighbor_dict['index']
            neighbor_symbol = list(neighbor_dict['species'].keys())[0]
            
            if neighbor_symbol == migrating_element:
                start_rep_idx = equivalent_atoms[start_idx]
                end_rep_idx = equivalent_atoms[end_idx]
                rounded_distance = round(distance, distance_precision)
                
                hop_type = (tuple(sorted((start_rep_idx, end_rep_idx))), rounded_distance)
                
                if hop_type not in processed_hop_types:
                    processed_hop_types.add(hop_type)
                    final_hops_to_generate.append((start_idx, end_idx))
                    
    return final_hops_to_generate
