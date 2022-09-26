""" A silly hello world example """

import os
import random
from . import hello_world

def Run(params, out_folder, job_id):
    """ Silly 'simulation' code """

    # This simply demonstrates how to load parameters. They are not used in this example except for diagnostics output.
    if params['diag']:
        dloc = tuple([int(x) for x in params['days_at_loc'].split(",")])

        f_diag = open(os.path.join(out_folder, str(job_id) + ".diag"), 'w')
        f_diag.write("SimLength::NrSites::DaysAtLocation::RandSeed::JobID\n")
        f_diag.write(str(params['sim_length']) + "::" + str(params['nr_sites']) + "::" +
                     str(dloc) + "::" + str(params['randseed']) + "::" + str(job_id) + "\n")
        f_diag.close()

    random.seed(params['randseed'])
    sleep_time = random.randint(2, 30)

    # Open output file and add a header
    f_res = open(os.path.join(out_folder, str(job_id) + ".csv"), 'w')
    f_res.write("EventID:FirstRand:Value\n")

    # Add results and close
    res = hello_world.hi(job_id, sleep_time)
    f_res.write("\n".join(res))
    f_res.close()

    return True
