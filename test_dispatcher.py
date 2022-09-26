# Tests basic functionality of the sim dispatcher using the default 'Hello world' sim.

import os
import sys
import numpy
import hashlib
import yaml

# Check for python version:
assert sys.version_info.major == 3, "Python 3.5 or above is required"
assert sys.version_info.minor > 5, "Python 3.5 or above is required"

# Set some expectations:
with open("test_config.yaml", "r") as f:
    test_cfg = yaml.safe_load(f)

# 1. Check the pickle (I don't see why the files wouldn't be the same, but easy to check, so why not):
assert hashlib.md5(open('configs/hydra.pkl','rb').read()).hexdigest() == hashlib.md5(open('out_results/conf.pkl','rb').read()).hexdigest()

# 2. Check that the required number of sim output files are present:
res = 0
for file in os.listdir("out_results/"):
    if file.endswith(".csv"):
        res = res + 1
assert res == test_cfg['exp_nrjobs']

# 2. Sanity checks on log file:
with open('out_results/jobs.log', 'r', newline='\n') as csvfile:
    j_log = csvfile.readlines()
j_log = [x.strip().split("::") for x in j_log]
j_head = j_log[0]
j_log = numpy.array(j_log[1:])

# 2.1 Check for unique combinations:
values, counts = numpy.unique(j_log[: , 0], return_counts=True) # Should be 4 unique x 10 with test sim
print("Unique combinations")
print(values)
print(counts)
assert len(values) == test_cfg['exp_nrcomb']
assert sum(counts) == test_cfg['exp_nrjobs']

# 2.2 Check that the rand seed is unique:
counts = numpy.unique(j_log[: , 6], return_counts=True)[1] # Rand seed
assert len(set(counts)) == 1, "Critical error: The same random seed used in two or more simulations"

# 2.3 Check that the job sequence numbers are unique
values, counts = numpy.unique(j_log[: , 5], return_counts=True) # Job seq id
#print(values)
#print(counts)
assert len(set(counts)) == 1


# 3. Check output of individual jobs, and make sure they match logs:
for i in range(0, j_log.shape[1]):

    # Check info recorded in the diag files
    diag_fn = j_log[i, 7].split(".")[0]
    with open("out_results/" + diag_fn + ".diag", "r", newline="\n") as diag_f:
        j_diag = diag_f.readlines()
    j_diag = j_diag[1].strip().split("::")

    #print(j_log[i, :])
    #print(j_diag)
    j_log_tmp = j_log[i, 1].split(",")
    j_log_tmp = str((int(j_log_tmp[0]), int(j_log_tmp[1])))
    assert j_log_tmp == j_diag[2], "Sim output for days at location does not match log file!"
    assert j_log[i, 4] == j_diag[0], "Sim output for time steps does not match log file!"
    assert j_log[i, 3] == j_diag[1], "Sim output for number of sites does not match log file!"
    assert j_log[i, 6] == j_diag[3], "Sim output for random seed does not match log file!"

    # Check info recorded in the sim output:
    with open("out_results/" + j_log[i, 7], "r", newline="\n") as sim_f:
        j_sim = sim_f.readlines()

    #print(j_sim)
    assert len(j_sim) == test_cfg['exp_sim_out_l'] + 1 # One for the header


print("All seems OK")


# TODO:
# Check that outputs match what was requested in the pickle file. Not critical: user should do basic sanity checks
# on their own sims. Plain good practice.