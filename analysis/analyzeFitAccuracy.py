from glob import glob

import matplotlib.pyplot as plt

import circlecalc
from holder import *

os.chdir("..")
tubepos = loadTubePos()

os.chdir(rootDataDir)

allDistances = []

for dir in glob("data_2017-*"):
    os.chdir(dir)

    analyzed = {}
    with open('analyzed.dum', 'r') as file:
        exec("analyzed = " + file.readline())

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
        if not len(tubeHitArray) == 4:
            # print(dir+"\\"+gon[:-4] + " does not have 4 tubehits, skipping")
            continue

        # **********************Get analyzed event data********************** #
        # this finds the analyzed data from the .dum file and pulls the information
        # however, if the dum file doesn't have this event, it means that the event had no valid tanlines
        # and therefore did not make an entry for it
        try:
            rawTanList, paddleTanList, bestTanLine, bestLine, cost = analyzed[gon]
        except KeyError:
            print(dir + "\\" + gon[:-4] + " has no valid tanlines, skipping")
            continue

        for tubehit in tubeHitArray:
            dist = circlecalc.distanceFromTubehitToTanline(tubehit, bestLine)
            # if dist <= OUTER_RADIUS:
            allDistances.append(dist / (10 ** -8 * DRIFT_VELOCITY))

    os.chdir("..")

os.chdir("../analysis/images")
(n, bins, patches) = plt.hist(allDistances, bins=round(max(allDistances)) + 1)

plt.ylim((0, 100))
plt.title("Magnitude of Error in Line Fit")
plt.xlabel("Number of Clock Cycles Error")
plt.ylabel("Number of Events with Given Error")
plt.savefig("FitAccuracy.png")
print(n)
