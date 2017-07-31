from holder import *
import numpy as np
import matplotlib.pyplot as plt

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

mindists = []

for j in range(10000):
    x0 = (np.random.rand()*(PADDLE_MAX_X-PADDLE_MIN_X))+PADDLE_MIN_X
    x1 = (np.random.rand()*(PADDLE_MAX_X-PADDLE_MIN_X))+PADDLE_MIN_X

    m = (PADDLE_MAX_Y-PADDLE_MIN_Y)/(x1-x0)
    b = PADDLE_MAX_Y - m*x1

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
        # record the closest distance found
        if not min(xdists.keys()) > OUTER_RADIUS:
            mindists.append(min(xdists.keys()))

plt.hist(mindists,bins=100)
plt.show()