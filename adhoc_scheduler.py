""" This script creates files usable by the dispatcher to run simulations on
ad hoc machines, using a given number of threads with a given set of parameter
combinations """

# NOTES:
# - doesn't handle allocations in the smartest way:
#   + type of sim should be scheduled according to the available memory.

import itertools
import pickle
import os
import yaml

with open("sim/sim_config.yaml", "r") as f:
    # NOTE: I don't think there is a point in using safe_load here. You execute code in sim/ anyway.
    sim_cfg = yaml.safe_load(f)

avail_threads = sim_cfg['RESOURCES']
params = sim_cfg['PARAMS']
nr_replicates = sim_cfg['SCHEDULER']['runs_per_cfg']
baseline_cpu = sim_cfg['SCHEDULER']['baseline_cpu']
baseline_perf = sim_cfg['SCHEDULER']['baseline_perf']

# Scheduling
# a. Produce combinations from given parameters
params_keys = sorted(params)
combs = [[{pname: val} for pname, val in zip(params_keys, prod)] for\
         prod in itertools.product(*(params[param] for\
                                     param in params_keys))]

# Add combination id, which can be used for seeding later
for i in range(0, len(combs)):
    combs[i].append({'comb_id': i})

av_cores = sum([val[0] for val in avail_threads.values()])
tot_sims = len(combs) * nr_replicates
tot_tsteps = tot_sims * params['sim_length'][0] #* ts_multiplier
# yes, it is a crude estimate:
exp_runtime = tot_tsteps / baseline_perf / 3600 / av_cores # In hrs
print("Scheduling " + str(tot_sims) + " simulations across " +\
      str(len(avail_threads)) + " machines (" + str(av_cores) + " cores). ")
print("Baseline predicted runtime: " + str(round(exp_runtime)) + " hours (" +\
      str(round(exp_runtime/24)) + " days)") 
print("")

# b. Assign combinations for each machine and save configs as pickles.
confpath = os.path.join(os.getcwd(), "configs")
try:
    os.mkdir(confpath)
except FileExistsError:
    print("Error: Output folder <" + confpath + "> exists. Remove it and re-run")
    exit(-1)

comb_units = [combs[i:i + av_cores] for i in range(0, len(combs), av_cores)]
mnames = [[mname for ncores in range(0, opts[0])] for\
          mname, opts in avail_threads.items()]
mnames = [mname for sublst in mnames for mname in sublst]
mjobs = {key: [] for key in avail_threads.keys()}
for unit in comb_units:
    req_cores = len(unit)
    for mid in range(0, req_cores):
        mjobs[mnames[mid]].extend([unit[mid]])

print("Job allocations:\n ")
for key, value in mjobs.items():
    print(str(key) + ": " + str(len(value)) + " parameter combinations (" +\
          str(len(value) * nr_replicates) + " simulations) ~ " +\
          str((len(value) * nr_replicates * params['sim_length'][0]) / \
              baseline_perf / 3600 / 24 / avail_threads[key][0]) + " days")
    if len(value) == 0:
        print("WARNING: No job assignments for " + key + ". Bypassing creation of .pkl file for this machine.")
        pass
    else:
        jconfig = {'specs': avail_threads[key],
                   'jobs': value,
                   'totaljobs': len(combs) * nr_replicates,
                   'reps': nr_replicates}
        pickle.dump(jconfig, open(os.path.join(confpath, key + ".pkl"), 'wb'))
print("")
print("Saved job configurations (.pkl files) to:\n" + str(confpath))

print("")
print("Please copy the appropriate .pkl file to the machine indicated by the "+\
      "file name")
print("")
