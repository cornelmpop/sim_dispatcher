# Tests basic functionality of the sim dispatcher using the default 'Hello world' sim.

import os
import sys
import subprocess
import yaml


# Check for python version:
assert sys.version_info.major == 3, "Python 3.5 or above is required"
assert sys.version_info.minor > 5, "Python 3.5 or above is required"

# Set some expectations:
with open("test_config.yaml", "r") as f:
    test_cfg = yaml.safe_load(f)

# The configs and out_results folders shouldn't exist when we run these tests.
assert os.path.isdir('configs') == False, "Found configs folder. This is unexpected."
assert os.path.isdir('out_results') == False, "Found out_results folder. This is unexpected."

## Part 1 - Check scheduler output:
# Run the scheduler:
try:
    sched = subprocess.check_output(["python", os.path.dirname(os.path.abspath(__file__)) + "./adhoc_scheduler.py"],
                                    universal_newlines=True)
except subprocess.CalledProcessError:
    print("Unexpected error while trying to run the adhoc_scheduler.py")
    exit(-1)

output_lines = sched.split("\n")

o_jobs = output_lines[0].split(" ")
assert o_jobs[1] == str(test_cfg['exp_nrjobs']), "Unexpected number of jobs."
assert o_jobs[4] == str(test_cfg['exp_nrmachines']), "Unexpected number of machines."

o_jobs = output_lines[1].split(" ")
# Expect 100 million time steps per sim at 20k time steps per second, in hours. Take the time each sim is expected to
# run for and multiply it by the number of sims (4 * 10 - see above)
assert o_jobs[3] == str(round(((100000000 / 20000 / 3600) * test_cfg['exp_nrjobs']) / test_cfg['exp_threads'])),\
    "Unexpected job length estimate."

o_warn = output_lines[7].split(" ")
assert o_warn[0] == "WARNING:", "Expected a warning about empty job allocations, but got none."

# Check that the scheduler reports and error if the output folder exists.
sched = subprocess.run(["python", os.path.dirname(os.path.abspath(__file__)) + "./adhoc_scheduler.py"])
assert sched.returncode in [4294967295, -1], "Expected error when running adhoc_scheduler with pre-existing configs"

print("All seems OK")