# The main script.  Run this script to analyze a folder of .gon event files
from glob import glob

import matplotlib.pyplot as plt
from numpy import loadtxt
import numpy as np

import circlecalc
from holder import *

# folder in which to find the data.  this can be relative or absolute path
dataDir = "runs/data_2017-07-28_1719/"
# subfolder name in which to put the images (will be generated as a subfolder of dataDir).  If it already exists,
# we'll try to make a different one
imgDir = "images"


# ******************Load tube position data***************** #
# using numpy, get the x,y positions of each tube in m.  load them into a dict using names as keys
# requires name to be converted from bytes to strings
tubepos = {}
tubeaxs = []
tubebxs = []
tubeys = []
for tube in loadtxt("tubepos.csv", delimiter=",", dtype="S3,f4,f4"):
    tubepos[tube[0].decode("utf-8")] = (tube[1], tube[2])
    if tube[0].decode("utf-8")[1] == 'A':
        tubeaxs.append(tube[1])
    else:
        tubebxs.append(tube[1])
    tubeys.append(tube[2])

tubeaxs = sorted(list(set(tubeaxs)))
tubebxs = sorted(list(set(tubebxs)))
tubeys = sorted(list(set(tubeys)))

minxdists = []
allTubeHits = []


# Move to the directory in which the data files are
os.chdir(dataDir)

# Iterate through every data file in the directory, generating an output image for them
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

    i = 1
    for y in tubeys:
        tubexs = []
        if i % 2 == 0:
            tubexs = tubeaxs
        else:
            tubexs = tubebxs
        xdists = []
        for x in tubexs:
            m = bestLine.m
            b = bestLine.b
            xdists.append(np.abs(b + m * x - y) / np.sqrt(1 + m ** 2))
        minxdists.append(min(xdists))
        i += 1


    print("Saved " + imgDir + "/" + gon[:-4] + ".png\n\r")

print(minxdists)
plt.hist(minxdists, bins=100)
plt.hist([tubehit.r for tubehit in allTubeHits], bins=100, alpha=0.5, color='red')
plt.show()



