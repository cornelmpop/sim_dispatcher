""" Runs simulations on the current machine, based on the pickled configuration
options set up by the scheduler script """

# NOTES:
# - output filenames not intuitive.
# - should log which combs are in which files, with basename set to out_res
# - FIXED. interrupted files should be deleted - actually, just overwrite from simulation.py
# SELF NOTES:
# - Sometimes when resuming jobs it saves to the same folder?!?
# -- Should output str(key)":" + val for key,val in dict.items() for each output folder! simple file.
import sys
import pickle
from multiprocessing import Process
import logging
import os
import hashlib # To check that the output matches the pickle.
import shutil
import copy
import uuid
import glob
import pairing

import time
from sim import simulation as simulation

# Yes, this is very crude, but it's only meant as a gentle reminder to the
# user that a pickle file has to be supplied as an argument. I don't see the
# point in doing more checks given the target user and the source of the
# pickles (made by the user, presumably just before running this file).
try:
    pkl_file = sys.argv[1]
except IndexError:
    exit("Usage: python " + sys.argv[0] + " <full path to .pkl file>")

try:
    pkl = open(pkl_file, 'rb')
    job_config = pickle.load(pkl)
    pkl.seek(0, 0)
    job_hash = hashlib.sha256(pkl.read()).hexdigest()
    pkl.close()
except FileNotFoundError:
    exit("Error: Configuration file <" + str(pkl_file) + "> not found")

# specs, jobs
av_cores = job_config['specs'][0]
av_mem = job_config['specs'][1]
jobs = job_config['jobs']
nr_reps = job_config['reps']

# Set up output, if necessary:
# Make sure that, if the output folder exists, it is for the right job. If
# it does not exist, record this job's hash so we can do the verification on subsequent runs:
out_folder = os.path.join(os.path.dirname(os.path.realpath(__file__)), "out_results")
hash_file = os.path.join(out_folder, "job_hash.txt")
try:
    os.makedirs(out_folder)
except FileExistsError:
    pass
else:
    # Yes, this could be a problem if the file changes during runtime. Should probably
    # be pickled from the loaded config (would also enable the pickles to be compared)
    shutil.copyfile(pkl_file, os.path.join(out_folder, "conf.pkl"))
    with open(hash_file, 'w') as f:
        f.write(str(job_hash))

if os.path.isdir(out_folder):
    try:
        with open(hash_file, 'r') as f:
            exp_hash = f.readline()
    except FileNotFoundError:
        exit("\nError: Output folder exists but no hash file for jobs")
    else:
        if exp_hash != str(job_hash):
            exit("\nError: Output folder wasn't created for this job!")
else:
    exit("\nError: Output folder doesn't exist and couldn't be created")

# Start logging proc:
# 1. Check if we're going to be logging to an existing non-empty file
#    or not:
logfile = os.path.join(out_folder, "jobs.log")
try:
    if os.stat(logfile).st_size == 0:
        emptylog = True
    else:
        emptylog = False
except FileNotFoundError:
    emptylog = True

logger = logging.getLogger('sim_dispatch')
logger.setLevel(logging.INFO)
hdlr = logging.FileHandler(logfile, delay=False)
hdlr.setLevel(logging.INFO)
hdlr.setFormatter(logging.Formatter('%(message)s'))
logger.addHandler(hdlr)

comp_job = "COMPLETED"
# Get job parameters here, so that we may write header to log if necessary:
job_keys = []
[job_keys.append(list(val.keys())[0]) for val in jobs[0]]
job_keys = sorted(job_keys)
job_keys_extra = ['seq_job_id', 'randseed', 'file', 'status']
if emptylog:
    # Get parameter keys and add to header to log:
    log_header = copy.copy(job_keys)
    log_header.extend(job_keys_extra)
    #print(len(log_header))
    logger.info("::".join(log_header))

# At this point the log file is set up. Now, we need to filter out finished jobs
def get_job_status(logfile):
    completed_jobs = []
    valid_files = []
    # The log file _should_ be there, otherwise assertion _should_ be raised!
    with open(logfile, 'r') as f:
        content = f.readlines()
    for lline in content[1:len(content)]:
        jvals = lline.strip().split("::")
        if len(jvals) != len(job_keys) + len(job_keys_extra):
            exit("Bad log file")
        if jvals[-1] == comp_job:
            completed_jobs.append(jvals[0:len(jvals) - len(job_keys_extra)])
            valid_files.append(jvals[-2])
    return ({'completed': completed_jobs,
             'comp_files': valid_files})


def run_sim(params, out_folder, comp_job):
    # This is the function that runs the individual sim jobs. What it does:
    # - assigns each run (including replicates) a unique ID.
    # - starts the simulation's Run function with the assigned unique ID and the passed parameters.
    # - logs completed job and reports run speed after the simulation concludes
    # NOTE: You CAN override parameters here, but you SHOULD NOT define them here.
    # print("Running")
    # params['create_rand_sites'] = True # This should NOT be defined here! BUT it may be overwritten
    # params['rand_prefetch_size'] = 400000
    job_str = "::".join([str(params[key]) for key in job_keys])
    job_id = str(uuid.uuid4())
    ## NOTE: Here I need something better than wunit and wsub, unless they are always
    ## guaranteed to be the same! What if I just save to the hash as folder
    ## name, ignoring the wunit/wsub deal altogether?

    timea = time.time()
    if simulation.Run(params, out_folder, job_id):
        logger.info(job_str + "::" + str(params['seq_job_id']) + "::" + str(params['randseed']) + "::" + job_id + ".csv" + "::" + comp_job)
        timeb = time.time()
        print("Ran at: " + str(round(params['sim_length'] / (timeb - timea))) + " time steps/sec")

# jobs is a list of dictionaries, which gets put back together into a single dict.
comp_jobs = get_job_status(logfile)

jobs_todo = []
for job in jobs:
    jdict = {}
    [jdict.update(val) for val in job]
    if len(job_keys) != len(jdict.keys()):
        exit("\nError: Keys in log file do not match job parameter keys")

    reps_to_do = nr_reps - comp_jobs['completed'].count([str(jdict[key]) for key in job_keys])
    for i in range(reps_to_do, 0, -1):
        jbrep = copy.copy(jdict)
        # POSSIBLE BUG: Am I keeping track of the rep IDs adequately? Should each individual job be assigned
        # an ID early on (e.g., in the pickle)?

        # NOTE: 202209 - There are better ways of doing this, but without this if/else the log/output files get out of
        # sync.
        if reps_to_do < nr_reps:
            jbrep['randseed'] = pairing.pair(jbrep['comb_id'], i - 1)
            jbrep['seq_job_id'] = pairing.pair(jbrep['comb_id'], i - 1)
        else: # 202209:
            jbrep['randseed'] = pairing.pair(jbrep['comb_id'], i)
            jbrep['seq_job_id'] = pairing.pair(jbrep['comb_id'], i)

        jobs_todo.extend([jbrep])


if __name__ == '__main__':
    work_units = [jobs_todo[i:i + av_cores] for i in range(0, len(jobs_todo), av_cores)]
    print("Jobs: " + str(len(comp_jobs['completed'])) + " done, " + str(len(jobs_todo)) + " pending")

    # Clean unreferenced files:
    # POSSIBLE BUG: Hard coded file extension. Simulations must output .csv for this to work.
    csv_files = [os.path.basename(i) for i in glob.glob(os.path.join(out_folder, '*.csv'))]
    orphans = (set(csv_files) - set(comp_jobs['comp_files']))
    missing = (set(comp_jobs['comp_files']) - set(csv_files))
    if len(missing) > 0:
        exit("ERROR: Output files for completed jobs are missing! Check the log.")
    if len(orphans) > 0:
        print("Orphan files detected! Removing...")
        [os.remove(os.path.join(out_folder, x)) for x in orphans]

    print("\nProceeding with tasks...")
    for wunit in range(0, len(work_units)):
        nr_threads = len(work_units[wunit])
        thjobs = {}
        for nthread in range(0, nr_threads):
            params = work_units[wunit][nthread]
            thjobs[nthread] = Process(target=run_sim, args=([params, out_folder, comp_job]))
            thjobs[nthread].start()

        for key in thjobs.keys():
            thjobs[key].join()
        print("============ WUNIT DONE ===========")


    print("Closing logger")
    logging.shutdown()
    print("\nAll tasks completed")
