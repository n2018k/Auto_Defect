Contents of Each File

io_step.py: For some reason, Gemini recommends that I run NEB from this file after setting NEB directory. Quite strange

main_workflow.py is the script to call initially by passing a crystal structure file as an ASE input file. Assumes only 3 images in NEB for now

relaxer_step.py is used for geometry optimization for bulks and vacancy

neb_step.py does the actual neb and barrier evaluation. It has hardcoded middle image as saddle for now

pathfinder_step.py finds all unique paths for me

supercell_step.py makes the supercell by making sure all box lengths are atleast 10Angs. This is a conscious choice for me

prefactor.py calls the routine for diffusion process prefactor based on Vineyard formulism

status_manager.py will check if a directory has already processed in case the main_workflow died. 


<img width="3298" height="4146" alt="graphviz_twopi" src="https://github.com/user-attachments/assets/d57d077a-2be1-4ec4-9f6c-00c5e72d8310" />
