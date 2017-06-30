# The main script.  Run this script to run the program
from holder import *
import circlecalc as cc
import numpy as np
import matplotlib.pyplot as plt

# define what to plot
plotTubes = True
plotHitCircles = True
plotPossibleTanLines = True

#******************Load tube position data*****************#
# get the x,y positions of each tube in m.  load them into a dict using names as keys
# requires name to be converted from bytes to strings
tubepos = {}
for tube in np.loadtxt("tubepos.csv", delimiter=",", dtype="S3,f4,f4"):
    tubepos[tube[0].decode("utf-8")] = (tube[1], tube[2])

#**********************Load event data**********************#
with open("sampledata/event1.gon", "r") as file:
    # list to be filled with tubehit events
    dataArray = []
    # Iterate through every line in the file
    for line in file:
        # takes line, removes the trailing \n, then creates a two element list split at the ;
        data = line[0:-1].split(";")

        # if it's code 256, meaning the tube didn't fire, ignore it, we don't care
        # otherwise, convert # of clock pulses into radius (m) and xref with the tube x,y pos to make a tubehit event
        if data[1] != "256":
            xy = tubepos[data[0]]
            dataArray.append(tubehit(xy[0], xy[1], float(data[1]) * 1e-8 * DRIFT_VELOCITY, data[0]))


#******************Find possible tan lines*******************#
# list to be filled with tanLine objects representing every possible tan line for every pair of tubehits
tanList = []
# fill tanList by iterating through every combination of tubehits
for i in range(len(dataArray)):
    for j in range(i+1, len(dataArray)):
        tanList = tanList + cc.possibleTan(dataArray[i], dataArray[j])



# ***********************Draw everything**********************#
# create the drawing
fig, ax = plt.subplots()
# draw all tubes if requested
if plotTubes:
    for name, pos in tubepos.items():
        ax.add_artist(plt.Circle(pos, OUTER_RADIUS, fill=False, color='black'))
# draw all hit circles if requested
if plotHitCircles:
    for hit in dataArray:
        ax.add_artist(plt.Circle((hit.x, hit.y), hit.r, fill=False, color='blue'))
# draw all possible tan lines if requested
if plotPossibleTanLines:
    for line in tanList:
        fig.plot([0, 1], [line.y(0), line.y(1)], color="green")
# size the drawing and save it
plt.xlim((0, 0.5))
plt.ylim((0, 0.5))
fig.savefig("name.png")
