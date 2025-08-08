this is an important tool for 

given a unit cell, this will optimize it, make supercell, optimize that cell
then find all symmetrically equivalent lithium positions, and select unique ones 
to find unique lithium paths, by creating individual directories for each
Then, it will take each directory and setup NEB and run it
it checks if GPU is available and restarts job if main_workflow died for some reason
and it also logs status of each directory upon its completion which is 
uesful in restarting job
I have also added a task to do climbing imaged NEB after regular NEB
this will ensure or try to ensure one image is on the top of the band always
The code will only do  this if regular neb converged otherwise it will exit
it will also a tags for barrier and prefactor in status file 
and also save vibrations for me in a dat file for future without need to run it again
It will try to run NEB with multiple methods and optimizer to try
its best and converge it within 5000 steps otherwise it will move to next step.

Extremely good and modular


io_step.py: For some reason, Gemini recommends that I run NEB from this file after setting NEB directory. Quite strange

main_workflow.py is the script to call initially by passing a crystal structure file as an ASE input file. Assumes only 3 images in NEB for now

relaxer_step.py is used for geometry optimization for bulks and vacancy

neb_step.py does the actual neb and barrier evaluation. It has hardcoded middle image as saddle for now

pathfinder_step.py finds all unique paths for me

supercell_step.py makes the supercell by making sure all box lengths are atleast 10Angs. This is a conscious choice for me

prefactor.py calls the routine for diffusion process prefactor based on Vineyard formulism

status_manager.py will check if a directory has already processed in case the main_workflow died. 


I have added a Result file for LGP structure to show what it should look like always. I also have a spodumene example which I will update here to show multiple lithium path example
That example is extremely important to work here


