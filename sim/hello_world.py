import time

def hi(job_id: int, sleep_time: int):
    """
    Say hi using the parameters passed from the simulation.py script, and take a pause. Taking a pause to slow down
    execution long enough to allow for some meaningful tests.

    @type job_id: int
    @type sleep_time: int
    """

    time.sleep(sleep_time)

    res = []
    for i in range(0, 10):
        res.append(str(i) + "::" + str(sleep_time) + "::Hello!")

    return res
