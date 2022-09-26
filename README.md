# SimDispatcher

A very simple way of distributing simulations across an ad-hoc, heterogeneous set of multi-core machines. The dispatching framework is resilient to failure - jobs can be resumed by simply running the dispatcher2.py script after a crash, power outage, etc., and the clean-up will be performed automatically.

DISCLAIMER: Please note that simplicity rather than optimization was my main goal in writing these scripts - I needed something that'd work, not necessarily something elegant. Some of the error checking is quite crude, and there are a few known issues (see below), but it should get the job done.

## Usage

0. Before you get stated, install the latest version of the Anaconda Python distribution and the pairings module (i.e., `pip3 install pairing`).

1. To run the included 'Hello World' simulation, first allocate jobs using the following command on one of the machines you intend to run the simulations on (note that the allocation is done based on the 'sim_config.yaml' configuration file stored in the "sim/" folder):

   > python adhoc_scheduler.py
   
The above command will create a new folder, 'configs', and it will place a .pkl file with job information for each of the machines specified in the RESOURCES section of the 'sim/sim_config.yaml' file. Note that the default configuration for the "hello world" simulation will only use one machine ("hydra"). Simply add another parameter in the PARAMS section if you want to see how the script behaves with jobs that need to be run on more than one machine.

Once you have run the above command, copy this folder to each of the other machines that will run simulations.

2. Run the jobs from a .pkl file stored in 'configs' (e.g., on a machine named Hydra, run "hydra.pkl" - this is the name used in the default configuration distributed here):

   > python dispatcher2.py configs/hydra.pkl
   
The above command will run the jobs specified in configs/hydra.pkl, placing the outputs in a new 'out_results' folder. In addition to the outputs of the simulations, this folder will also contain:

   1. conf.pkl: a copy of the pkl file used to run the jobs in this folder (i.e., this is the file specified in the argument passed to dispatcher2.py)
   2. job_hash.txt: contains a hash of the pickle file containing the job configuration. Unique for each job parameter setup, not for each run of the adhoc_scheduler.py (unless the code of the scheduler changes, of course). Different configurations == different pickles == different hashes. This is how the dispatcher2.py file knows it is working on the right job after interruptions.
   3. jobs.log: Keeps a log of completed jobs. Incomplete jobs will not appear here, so the dispatcher will attempt to re-run them if restarted. If you want to see how the dispatcher deals with unexpected interruptions (e.g., a power outage), simply stop the process and re-run the above command.

3. Run some basic sanity checks (note: you may have to adjust the test_config.yaml file if you modify 'sims/sim_config.yaml'):

   > python test_dispatcher.py

## NOTES:

- The dispatcher will keep on running even if individual simulation jobs encounter errors and die. This is as I intended. Only completed jobs will be logged to the jobs.log file.
- Orphaned job outputs (.csv files in out_results) will be deleted by dispatcher2.py (i.e., if the hash is not in the log file marked as complete).
- IMPORTANT: Make sure you do basic sanity checks on the outputs of your simulation. The scheduler should work, but I offer no guarantees. Check the output of your simulations to make sure they are what you expect to see.

## KNOWN ISSUES:

- Simulations *must* output .csv files, otherwise things may break.
- (BUG) Sometimes the jobs seem to finish without any issues, and yet the sanity check fails because the log file is missing information on one of the simulations. Simply run `python dispatcher2.py configs/hydra.pkl` (or whatever your .pkl is called) again; that should fix the problem, though it does run one extra job.
- (BUG) Sometimes an empty line gets placed in the log file (usually at the end). You will have to edit the log file and remove the empty line as well as the line for the last job, and re-run the dispatcher script.
- (BUG) Sometimes (e.g., on interruption), a simulation may be started with a random seed that has already been assigned to another simulation. This will be apparent in the log file, and the job will not pass the test_dispatcher.py checks. Currently, the fix requires deleting all replicates of a given parameter combination from the log file. This is something that I will try to fix soon. The problem is caused by the naive way in which random seeds are allocated to incomplete jobs.
