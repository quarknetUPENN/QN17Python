# A script to analyze all data files and produce two graphs of overall system performance
from glob import glob

import matplotlib.pyplot as plt
import numpy as np
from scipy.special import factorial

from analysis import outputFolder
from holder import *

# a dictionary to record the number of times any given tube gets hit
tubeHitCounts = {}

# a list of how many events have a given number of hits
# the number in the 0th place represents the number of events that had 0 hits, etc
hit_count_dist = list(np.zeros(32))

tubepos = {}
for tube in np.loadtxt("tubepos.csv", delimiter=",", dtype="S3,f4,f4"):
    tubepos[tube[0].decode("utf-8")] = (tube[1], tube[2])
    tubeHitCounts[tube[0].decode("utf-8")] = 0

os.chdir(rootDataDir)
for dir in glob("data_2017-*"):
    # Move to the directory in which the data files are
    os.chdir(dir)

    # Iterate through every data file in the directory, generating an output image for them
    for gon in glob("*.gon"):
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
                    tubeHitCounts[data[0]] += 1
        hit_count_dist[len(tubeHitArray)] += 1

        if len(tubeHitArray) <= 1:
            print(dir[16:] + "," + gon[:-4] + " has no real tubehits")
            continue
    os.chdir("..")
os.chdir("..")


# draw the number of triggers recorded for every tube
tubeList = []
triggerList = []
for key in sorted(tubeHitCounts.keys()):
    tubeList.append(key)
    triggerList.append(tubeHitCounts[key])
plt.barh(np.arange(len(tubeHitCounts)), triggerList, tick_label=tubeList)
plt.xlabel("Number of Triggers Recorded")
plt.ylabel("Tube Code")
plt.savefig(outputFolder+"TubeHitFrequency.png")
plt.cla()

while hit_count_dist[-1] == 0:
    hit_count_dist.pop()

expected_hit_count_dist = []
p = 0.3
pnoise = 0.03
for i in range(5):
    expected_hit_count_dist.append(sum(hit_count_dist) * p ** i * (1 - p) ** (4 - i) * factorial(4)/(factorial(i)*factorial(4-i)))


anotherList = list(np.zeros(len(hit_count_dist)+1))
for i in range(len(expected_hit_count_dist)):
    anotherList[i] += (1-pnoise)*expected_hit_count_dist[i]
    anotherList[i+1] += pnoise*expected_hit_count_dist[i]

plt.bar(range(len(hit_count_dist)), hit_count_dist)
plt.xlim((0,5))
#plt.bar(range(len(anotherList)), anotherList, color='r', alpha=0.5)
plt.xlabel("Number of Tube Hits per Event")
plt.ylabel("Number of Events")
plt.savefig(outputFolder+"OverallHitCountDistribution.png")
