# The main script.  Run this script to analyze a folder of .gon event files
from glob import glob

import matplotlib.pyplot as plt
from numpy import loadtxt
from numpy import savetxt

import circlecalc
from holder import *

# folder in which to find the data.  this can be relative or absolute path
dataDir = "runs/data_2017-07-30_1741/"
# subfolder name in which to put the images (will be generated as a subfolder of dataDir).  If it already exists,
# we'll try to make a different one
imgDir = "images"

analyzedFiles = []
def formatTanlineList(tanlineList):
    output = "["
    for line in tanlineList:
        output += formatTanline(line) + ","
    return output[:-1] + "]"


def formatTanline(tanline):
    return "tanLine(" + str(tanline.m) + "," + str(tanline.b) + ")"


# ******************Load tube position data***************** #
# using numpy, get the x,y positions of each tube in m.  load them into a dict using names as keys
# requires name to be converted from bytes to strings
tubepos = {}
for tube in loadtxt("tubepos.csv", delimiter=",", dtype="S3,f4,f4"):
    tubepos[tube[0].decode("utf-8")] = (tube[1], tube[2])

# Move to the directory in which the data files are
os.chdir(dataDir)
# Make the image directory, even if it's not exactly the specified one
imgDir = makeImgDir(imgDir)

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
    if not len(tubeHitArray) <= 1:
        print(gon[:-4] + " has no real tubehits, skipping")
        continue

    # **********************Analyze event data********************** #
    results = circlecalc.analyzeHits(tubeHitArray, verbose=True)
    if results[-1] is None:
        print(gon[:-4] + " has no valid tanlines, skipping")
        continue
    else:
        rawTanList, paddleTanList, bestTanLine, bestLine, cost = results

    analyzedFiles.append("\""+gon+"\"" + ": [" + formatTanlineList(rawTanList) + "," + formatTanlineList(paddleTanList) + "," +
        formatTanline(bestTanLine) + "," + formatTanline(bestLine) + "," +
        str(min(cost.keys())) + "]")

    # ***********************Draw everything********************** #
    # create the drawing
    fig, ax = plt.subplots()
    # draw all tubes if requested
    if plotConfig["showTubes"]:
        for name, pos in tubepos.items():
            ax.add_artist(plt.Circle(pos, OUTER_RADIUS, fill=False, color='black'))
            if plotConfig["showTubeLabels"]:
                ax.text(pos[0], pos[1], name, size=8, ha="center", va="center", alpha=0.5)
    # draw all hit circles if requested
    if plotConfig["showHitCircles"]:
        for hit in tubeHitArray:
            if hit.r <= 3 * 1e-8 * DRIFT_VELOCITY:
                ax.add_artist(plt.Circle((hit.x, hit.y), 3 * 1e-8 * DRIFT_VELOCITY, fill=True, color='red', lw=1.5))
            else:
                ax.add_artist(plt.Circle((hit.x, hit.y), hit.r, fill=False, color='red', lw=1.5))
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
    # draw all the lines that were searched around the tan line
    if plotConfig["showSearchedLines"]:
        for line in cost.values():
            lab, = ax.plot([0, 1], [line.y(0), line.y(1)], color="yellow", lw=0.01)
        lab.set_label("Searched Lines")
    # draw the best guess at the particle's track if requested
    if plotConfig["showBestLine"]:
        lab, = ax.plot([0, 1], [bestLine.y(0), bestLine.y(1)], color="blue", lw=2)
        lab.set_label("Best Line")

    # draw legend to right of graph
    lgd = ax.legend(loc='center left', bbox_to_anchor=(1, 0.5))

    # size the drawing and save it into the imgDir
    ax.set_xlim((0.0, 0.7))
    ax.set_ylim((0.0, 0.7))
    fig.savefig(imgDir + "/" + gon[:-4] + ".png", bbox_extra_artists=(lgd,), bbox_inches="tight")
    plt.close(fig)
    print("Saved " + imgDir + "/" + gon[:-4] + ".png\n\r")
os.chdir("../..")

with open('thing.dum', 'w') as f:
    f.write("{")
    writeString = []
    for string in analyzedFiles:
        writeString.append(string)
        writeString.append(", ")
    for string in writeString[:-1]:
        f.write(string)
    f.write("}")

