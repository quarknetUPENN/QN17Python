# The main script.  Run this script to analyze a .gon event file
from holder import *
import circlecalc as cc
import numpy as np
import matplotlib.pyplot as plt

# define what to plot
plotTubes = True
plotTubeLabels = True
plotPaddles = True
plotHitCircles = True
plotAllPossibleTanLines = True
plotPaddleTanLines = True
plotAverageTanLine = True

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
rawTanList = []
# fill tanList by iterating through every combination of tubehits
for i in range(len(dataArray)):
    for j in range(i+1, len(dataArray)):
        rawTanList = rawTanList + cc.possibleTan(dataArray[i], dataArray[j])
# list filled with tanLine objects representing only lines that pass through both paddles
paddleTanList = cc.removeSideTanLines(rawTanList)
# look for avg tan line in terms of slope, intercept
m, b = 0, 0
for line in paddleTanList:
    m = m + line.m
    b = b + line.b
# the average tan line
avgLine = tanLine(m/len(paddleTanList), b/len(paddleTanList))

# ***********************Draw everything**********************#
# create the drawing
fig, ax = plt.subplots()
# draw all tubes if requested
if plotTubes:
    for name, pos in tubepos.items():
        ax.add_artist(plt.Circle(pos, OUTER_RADIUS, fill=False, color='black'))
        if plotTubeLabels:
            ax.text(pos[0], pos[1], name, size=8, ha="center", va="center")
# draw all hit circles if requested
if plotHitCircles:
    for hit in dataArray:
        ax.add_artist(plt.Circle((hit.x, hit.y), hit.r, fill=False, color='blue'))
# draw both paddles if requested
if plotPaddles:
    ax.plot([PADDLE_MIN_X, PADDLE_MAX_X], [PADDLE_MIN_Y, PADDLE_MIN_Y], color='black', lw=10, label="Scintillator Paddle")
    ax.plot([PADDLE_MIN_X, PADDLE_MAX_X], [PADDLE_MAX_Y, PADDLE_MAX_Y], color='black', lw=10)
# draw all possible tan lines if requested
if plotAllPossibleTanLines:
    for line in rawTanList:
        lab, = ax.plot([0, 1], [line.y(0), line.y(1)], color="green", ls="--", lw=0.5)
    lab.set_label("All Tangent Lines")
# draw all tan lines through paddle if requested
if plotPaddleTanLines:
    for line in paddleTanList:
        lab, = ax.plot([0, 1], [line.y(0), line.y(1)], color="green", ls="-", lw=1)
    lab.set_label("Paddle Tangent Lines")
# draw average tan line if requested
if plotAverageTanLine:
    lab, = ax.plot([0, 1], [avgLine.y(0), avgLine.y(1)], color="red", ls="-", lw=2)
    lab.set_label("Average Tangent Line")
# draw legend to right of graph
lgd = ax.legend(loc='center left', bbox_to_anchor=(1, 0.5))


# size the drawing and save it
plt.xlim((0, 0.5))
plt.ylim((0, 0.5))
fig.savefig("name.png", bbox_extra_artists=(lgd,), bbox_inches="tight")
