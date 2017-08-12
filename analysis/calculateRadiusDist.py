import matplotlib.pyplot as plt
import numpy as np

from holder import *

# a dictionary mapping the tube name to a tuple (x,y) of its physical location in x and y
tubepos = {}
# a list of all the possible x coordinates for the set of tubes on layer A
tubeaxs = []
# a list of all the possible x coordinates for the set of tubes on layer B
tubebxs = []
# a list of all the possible y coordinates for all tubes
tubeys = []

os.chdir("..")
# fill all those variables above
for tube in np.loadtxt("tubepos.csv", delimiter=",", dtype="S3,f4,f4"):
    tubepos[tube[0].decode("utf-8")] = (tube[1], tube[2])
    if tube[0].decode("utf-8")[1] == 'A':
        tubeaxs.append(tube[1])
    else:
        tubebxs.append(tube[1])
    tubeys.append(tube[2])

# ensure that only sorted, unique values survive.  sorting is just for readability
tubeaxs = sorted(list(set(tubeaxs)))
tubebxs = sorted(list(set(tubebxs)))
tubeys = sorted(list(set(tubeys)))

# a list to be filled with all the tube hit radii that should have occurred
mindists = []

# make a random track and add all its theoritical hits to mindists.  10000 times.
for j in range(10000):
    # pick a random point on the upper and lower scintillator paddles
    x0 = (np.random.rand() * (PADDLE_MAX_X - PADDLE_MIN_X)) + PADDLE_MIN_X
    x1 = (np.random.rand() * (PADDLE_MAX_X - PADDLE_MIN_X)) + PADDLE_MIN_X

    # find the m and b for a line between those two above points.  this is a simulated random cosmic ray
    m = (PADDLE_MAX_Y - PADDLE_MIN_Y) / (x1 - x0)
    b = PADDLE_MAX_Y - m * x1

    # go through and figure out which tubes should have fired.  see analyzeTubeFail for an in depth explanation
    i = 0
    for y in tubeys:
        i += 1
        tubexs = []
        if i % 2 == 0:
            tubexs = tubeaxs
        else:
            tubexs = tubebxs

        xdists = {}
        for x in tubexs:
            xdists[(np.abs(b + m * x - y) / np.sqrt(1 + m ** 2))] = x

        # record the closest distance found if it's within a radius
        if not min(xdists.keys()) > OUTER_RADIUS:
            mindists.append(min(xdists.keys()) / (10 ** -8 * DRIFT_VELOCITY))

# draw, label, and save a histogram
plt.hist(mindists, bins=22)
plt.title("Expected Distribution of Tube Hit Radii")
plt.xlabel("Radius, in Clock Cycles")
plt.ylabel("Number of Hits")
plt.savefig("analysis/images/simulatedRadiusDist.png")
