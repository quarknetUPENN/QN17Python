from glob import glob

import matplotlib.pyplot as plt
from numpy import loadtxt
import numpy as np

import circlecalc
from holder import *

# folder in which to find the data.  this can be relative or absolute path
dataDir = "runs"

# a dictionary mapping the tube name to a tuple (x,y) of its physical location in x and y
tubepos = {}
# a dictionary that's the reverse of tubepos - mapping the tuple (x,y) of its physical location to the tube name
reverseTubePos = {}
# a dictionary that maps the tube name to the number of times it fails to fire when it should
tubeFailFreq = {}
# a dictionary that maps the tube name to the number of times it fires when it should
tubeNotFailFreq = {}
# a list of all the possible x coordinates for the set of tubes on layer A
tubeaxs = []
# a list of all the possible x coordinates for the set of tubes on layer B
tubebxs = []
# a list of all the possible y coordinates for all tubes
tubeys = []

# fill all those variables above
for tube in loadtxt("tubepos.csv", delimiter=",", dtype="S3,f4,f4"):
    tubepos[tube[0].decode("utf-8")] = (tube[1], tube[2])
    reverseTubePos[(round(tube[1], 4), round(tube[2], 4))] = tube[0].decode("utf-8")
    tubeFailFreq[tube[0].decode("utf-8")] = 0
    tubeNotFailFreq[tube[0].decode("utf-8")] = 0
    if tube[0].decode("utf-8")[1] == 'A':
        tubeaxs.append(tube[1])
    else:
        tubebxs.append(tube[1])
    tubeys.append(tube[2])

# ensure that only sorted, unique values survive.  sorting is just for readability
tubeaxs = sorted(list(set(tubeaxs)))
tubebxs = sorted(list(set(tubebxs)))
tubeys = sorted(list(set(tubeys)))

minxdists = []
allTubeHits = []

# Move to the directory in which the data files are
os.chdir(dataDir)

for dir in glob("data_*"):
    os.chdir(dir)
    # Iterate through every data file in the directory, processing them
    for gon in glob("*.gon"):
        # **********************Load event data********************** #
        with open(gon, "r") as file:
            # list to be filled with tubehit events
            tubeHitArray = []
            # Iterate through every line in the file
            for line in file:
                # takes line, removes the trailing \n, then creates a two element list split at the ;
                data = line[0:-1].split(";")

                # if it's code 255, meaning the tube didn't fire, ignore it
                # if the radius is larger than the tube, ignore it
                # if the tube is blacklisted, ignore it
                if not (data[1] == "255" or int(data[1]) > 22 or data[0] in tubeBlacklist):
                    # get the xy pos of the specified tube
                    xy = tubepos[data[0]]
                    # the radius being 0 causes errors, so don't let it be 0
                    if data[1] == "0":
                        radius = WIRE_RADIUS
                    else:
                        radius = float(data[1]) * 1e-8 * DRIFT_VELOCITY
                    tubeHitArray.append(tubeHit(xy[0], xy[1], radius, data[0]))
                    allTubeHits.append(tubeHit(xy[0], xy[1], radius, data[0]))
        if len(tubeHitArray) <= 1:
            print(gon[:-4] + " has no real tubehits, skipping")
            continue

        # **********************Analyze event data********************** #
        results = circlecalc.analyzeHits(tubeHitArray, verbose=True)
        if results[-1] is None:
            print(gon[:-4] + " has no valid tanlines, skipping")
            continue
        else:
            rawTanList, paddleTanList, bestTanLine, bestLine, cost = results

        # a counter variable to keep track of whether we are on layer a or b as we go through y
        i = 0
        # go through the event layer by layer.  A particle ideally will leave one hit on each y layer
        for y in tubeys:
            i += 1

            # if we recorded a hit on this layer, go figure out where it was.  Mark it down that this tube worked, then end
            if y in [tubehit.y for tubehit in tubeHitArray]:
                for tubehit in tubeHitArray:
                    if y == tubehit.y:
                        tubeNotFailFreq[tubehit.tube] += 1
                continue

            # figure out if the set of x coords we are on is A or B, and assign accordingly
            tubexs = []
            if i % 2 == 0:
                tubexs = tubeaxs
            else:
                tubexs = tubebxs

            # since we didn't record a hit on this layer and we should've, figure out what the radius should have been
            xdists = {}
            # go through every tube on the layer, and record the distance between the line and each tube
            for x in tubexs:
                m = bestLine.m
                b = bestLine.b
                xdists[(np.abs(b + m * x - y) / np.sqrt(1 + m ** 2))] = x
            # record the closest distance found
            minxdists.append(min(xdists.keys()))

            # look up the tube, and mark that it failed
            tubeFailFreq[reverseTubePos[(xdists[min(xdists.keys())], y)]] += 1
        print("Processed " + gon[:-4])
    os.chdir("..")
os.chdir("..")


(n, bins, patches) = plt.hist([round(x / (DRIFT_VELOCITY * 10 ** (-8))) for x in minxdists],
                              bins=round(max(minxdists) / (DRIFT_VELOCITY * 10 ** (-8))), label="Missed Tube Hits")
plt.hist([round(tubehit.r / (DRIFT_VELOCITY * 10 ** (-8))) for tubehit in allTubeHits], bins=bins, alpha=0.5,
         color='red', label="Recorded Tube Hits")
plt.xlabel("Radius in Clock Cycles")
plt.ylabel("Number of Events Recorded")
plt.title("Tube Miss Rate vs Hit Radius")
plt.savefig("TubeMissRateRadius.png")
plt.cla()


tubeList = []
triggerList = []
for key in sorted(tubeFailFreq.keys()):
    tubeList.append(key)
    triggerList.append(tubeFailFreq[key]/(tubeNotFailFreq[key]+tubeFailFreq[key]))
plt.barh(np.arange(len(tubeFailFreq)), triggerList, tick_label=tubeList)
plt.xlabel("Fraction of Missed Events")
plt.ylabel("Tube Code")
plt.title("Tube Miss Rate vs Tube Code")
plt.savefig("TubeMissRateCode.png")