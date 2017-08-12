# A script to analyze all data files and produce two graphs of overall system performance
from glob import glob

import matplotlib.pyplot as plt
import numpy as np

from analysis import outputFolder
from holder import *

# a dictionary mapping the tube code to the number of times it is hit
tubeHitCounts = {}

# a list of how many events have a given number of hits
# the number in the 0th place represents the number of events that had 0 hits, etc
hit_count_dist = list(np.zeros(32))

tubepos = loadTubePos()
for tube in np.loadtxt("tubepos.csv", delimiter=",", dtype="S3,f4,f4"):
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
                    # if a tube got hit, mark it as being hit
                    tubeHitCounts[data[0]] += 1
        # count the number of tube hits that were recorded and say that this event falls under that category
        # in hit_count_dist
        hit_count_dist[len(tubeHitArray)] += 1

        if len(tubeHitArray) <= 1:
            print(dir[16:] + "," + gon[:-4] + " has no real tubehits")
            continue
    os.chdir("..")
os.chdir("..")

# draw the number of triggers recorded for every tube:
# parse the tubeHitCounts dictionary
# a list of every tube code
tubeList = []
# a list of the number of times that a particular tube fired.  The particular tube has the same index as its index in
# tubeList.  ie, tubeList and triggerList have the same order
triggerList = []
# fill the lists
for key in sorted(tubeHitCounts.keys()):
    tubeList.append(key)
    triggerList.append(tubeHitCounts[key])

# draw the tube hits as a horizontal bar graph (so the tube labels have space)
# also add titles and axis labels and stuff
plt.barh(np.arange(len(tubeHitCounts)), triggerList, tick_label=tubeList)
plt.xlabel("Number of Events Recorded")
plt.ylabel("Tube Code")
plt.title("Number of Events Recorded Per Tube")
plt.savefig(outputFolder + "TubeHitFrequency.png")
plt.cla()

# draw hit_count_dist as a histogram:
# remove all trailing 0s from hit_count_dist to make it format nicer on the graph
while hit_count_dist[-1] == 0:
    hit_count_dist.pop()
# actually graph this and titles, axis labels, etc
plt.bar(range(len(hit_count_dist)), hit_count_dist)
plt.xlim((0, 5))
plt.xlabel("Number of Tube Hits per Event")
plt.ylabel("Number of Events")
plt.title("Number of Events with X Tubehits")
plt.savefig(outputFolder + "OverallHitCountDistribution.png")


# This used to calculate the expected distribution of hits given a probabiltiy of a noise hit in any event (pnoise)
# and the probability of a good tube hit (p) for any tube passage.  It used a binomial model and graphed it as a bar graph
# as a translucent red overlay over the current graph.  We didn't want it to show up right now but the code still works
# expected_hit_count_dist = []
# p = 0.3
# pnoise = 0.03
# for i in range(5):
#     expected_hit_count_dist.append(
#         sum(hit_count_dist) * p ** i * (1 - p) ** (4 - i) * factorial(4) / (factorial(i) * factorial(4 - i)))
#
# anotherList = list(np.zeros(len(hit_count_dist) + 1))
# for i in range(len(expected_hit_count_dist)):
#     anotherList[i] += (1 - pnoise) * expected_hit_count_dist[i]
#     anotherList[i + 1] += pnoise * expected_hit_count_dist[i]
# plt.bar(range(len(anotherList)), anotherList, color='r', alpha=0.5)
