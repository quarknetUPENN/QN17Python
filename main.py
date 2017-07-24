# The main script.  Run this script to analyze a folder of .gon event files
import os
from glob import glob

import matplotlib.pyplot as plt
from numpy import loadtxt

import circlecalc as cc
import tanlineoptimizer as tlo
from holder import *

# folder in which to find the data.  this can be relative or absolute path
dataDir = "sampledata/"
# subfolder name in which to put the images (will be generated as a subfolder of dataDir.  If it already exists
# in dataDir, it will be OVERWRITTEN
imgDir = "images"
# define what to plot
plotConfig = {"showTubes": True,
              "showTubeLabels": True,
              "showPaddles": True,
              "showHitCircles": True,
              "showAllPossibleTanLines": False,
              "showPaddleTanLines": False,
              "showBestTanLine": False,
              "showBestTanLineMidpoint": False,
              "showSearchedLines": False,
              "showBestLine": True}
# define what spread and how many points to iterate around the best tanline for various attributes
scanParams = {"m": scanParam(0.2, 10, True),
              "x": scanParam(0.01, 10, True),
              "y": scanParam(0.005, 10, True)}

# ******************Load tube position data***************** #
# using numpy, get the x,y positions of each tube in m.  load them into a dict using names as keys
# requires name to be converted from bytes to strings
tubepos = {}
for tube in loadtxt("tubepos.csv", delimiter=",", dtype="S3,f4,f4"):
    tubepos[tube[0].decode("utf-8")] = (tube[1], tube[2])

# Move to the directory in which the data files are
os.chdir(dataDir)
# Make a directory to fill with the produced images.  if it already exists, overwrite!
os.makedirs(imgDir, exist_ok=True)
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

            # if it's code 256, meaning the tube didn't fire, ignore it, we don't care
            # otherwise convert # of clock pulses into radius (m) and xref with the tube x,y pos to make a tubehit event
            if data[1] != "256":
                xy = tubepos[data[0]]
                tubeHitArray.append(tubehit(xy[0], xy[1], float(data[1]) * 1e-8 * DRIFT_VELOCITY, data[0]))

    # ******************Find possible tan lines******************* #
    # list to be filled with tanLine objects representing every possible tan line for every pair of tubehits
    rawTanList = []
    # fill tanList by iterating through every combination of tubehits
    for i in range(len(tubeHitArray)):
        for j in range(i + 1, len(tubeHitArray)):
            rawTanList = rawTanList + cc.possibleTan(tubeHitArray[i], tubeHitArray[j])
    # list filled with tanLine objects representing only lines that pass through both paddles
    paddleTanList = cc.removeSideTanLines(rawTanList)

    # *********************Find best tan line********************** #
    # calculate which tanline has the lowest cost
    # make a dictionary in which the keys are costs and the values are the tanlines that produced those costs
    cost = {}
    for line in paddleTanList:
        cost[tlo.tanlineCostCalculator(line, tubeHitArray)] = line
    # then find the minimum cost and figure out which tanline it was
    bestTanLine = cost[min(cost.keys())]

    # ***************Search around the best tan line*************** #
    # brute force down lists of lines around the best tanline to find the one with lowest cost
    # x,y is the x,y deviation from the midpoint, calculated relative to the scintillator paddles
    # m is the deviation from the slope of the best tanline
    cost = {tlo.tanlineCostCalculator(bestTanLine, tubeHitArray): bestTanLine}
    midpoint = [(bestTanLine.x((PADDLE_MIN_Y + PADDLE_MAX_Y) / 2)), (PADDLE_MIN_Y + PADDLE_MAX_Y) / 2]
    for m2 in scanParams["m"].range(bestTanLine.m):
        for x2 in scanParams["x"].range(midpoint[0]):
            for y2 in scanParams["y"].range(midpoint[1]):
                line = tanLine(m2, y2 - (m2 * x2))
                cost[tlo.tanlineCostCalculator(line, tubeHitArray)] = line

    # Our best guess at the particle's track!
    bestLine = cost[min(cost.keys())]

    # ***********************Draw everything********************** #
    # create the drawing
    fig, ax = plt.subplots()
    # draw all tubes if requested
    if plotConfig["showTubes"]:
        for name, pos in tubepos.items():
            ax.add_artist(plt.Circle(pos, OUTER_RADIUS, fill=False, color='black'))
            if plotConfig["showTubeLabels"]:
                ax.text(pos[0], pos[1], name, size=8, ha="center", va="center")
    # draw all hit circles if requested
    if plotConfig["showHitCircles"]:
        for hit in tubeHitArray:
            ax.add_artist(plt.Circle((hit.x, hit.y), hit.r, fill=False, color='green', lw=1.5))
    # draw both paddles if requested
    if plotConfig["showPaddles"]:
        ax.plot([PADDLE_MIN_X, PADDLE_MAX_X], [PADDLE_MIN_Y, PADDLE_MIN_Y], color='black', lw=10,
                label="Scintillator Paddle")
        ax.plot([PADDLE_MIN_X, PADDLE_MAX_X], [PADDLE_MAX_Y, PADDLE_MAX_Y], color='black', lw=10)
    # draw all possible tan lines if requested
    if plotConfig["showAllPossibleTanLines"]:
        for line in rawTanList:
            lab, = ax.plot([0, 1], [line.y(0), line.y(1)], color="green", ls="--", lw=0.5)
        lab.set_label("All Tangent Lines")
    # draw all tan lines through paddle if requested
    if plotConfig["showPaddleTanLines"]:
        for line in paddleTanList:
            lab, = ax.plot([0, 1], [line.y(0), line.y(1)], color="green", ls="-", lw=1)
        lab.set_label("Paddle Tangent Lines")
    # draw the best tan line if requested
    if plotConfig["showBestTanLine"]:
        lab, = ax.plot([0, 1], [bestTanLine.y(0), bestTanLine.y(1)], color="b", lw=1)
        lab.set_label("Best Tangent Line")
    # draw the midpoint of the best tan line if requested
    if plotConfig["showBestTanLineMidpoint"]:
        ax.scatter([midpoint[0]], [midpoint[1]], label="Best Tangent Line Midpoint")
    # draw all the lines that were searched around the tan line
    if plotConfig["showSearchedLines"]:
        for line in cost.values():
            lab, = ax.plot([0, 1], [line.y(0), line.y(1)], color="b", lw=0.01)
        lab.set_label("Searched Lines")
    # draw the best guess at the particle's track if requested
    if plotConfig["showBestLine"]:
        lab, = ax.plot([0, 1], [bestLine.y(0), bestLine.y(1)], color="r", lw=2)
        lab.set_label("Best Line")

    # draw legend to right of graph
    lgd = ax.legend(loc='center left', bbox_to_anchor=(1, 0.5))

    # size the drawing and save it into the imgDir
    ax.set_xlim((0.0, 0.5))
    ax.set_ylim((0.0, 0.5))
    fig.savefig(imgDir + "/" + gon[:-4] + ".png", bbox_extra_artists=(lgd,), bbox_inches="tight")
    print("Saved " + imgDir + "/" + gon[:-4] + ".png")
