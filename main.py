# The main script.  Run this script to analyze a folder of .gon event files
from glob import glob

import eventdraw

import circlecalc
from holder import *


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
tubePos = loadTubePos()

os.chdir("runs")

for dir in glob("data_2017-08-09*"):
    os.chdir(dir)
    # Make the image directory, even if it's not exactly the specified one
    imgDir = makeImgDir(imgDir)
    # Iterate through every data file in the directory, generating an output image for them
    for gon in glob("*.gon"):
        # **********************Load event data********************** #
        allCodes = []
        with open(gon, "r") as file:
            # list to be filled with tubehit events
            tubeHitArray = []
            # Iterate through every line in the file
            for line in file:
                # takes line, removes the trailing \n, then creates a two element list split at the ;
                data = line[0:-1].split(";")
                allCodes.append(data[0])

                # if it's code 255, meaning the tube didn't fire, ignore it
                # if the radius is larger than the tube, ignore it
                # if the tube is blacklisted, ignore it
                if not (data[1] == "255" or int(data[1]) > 22 or data[0] in tubeBlacklist):
                    # get the xy pos of the specified tube
                    xy = tubePos[data[0]]
                    # the radius being 0 causes errors, so don't let it be 0
                    if data[1] == "0":
                        radius = WIRE_RADIUS
                    else:
                        radius = float(data[1]) * 1e-8 * DRIFT_VELOCITY
                    tubeHitArray.append(tubeHit(xy[0], xy[1], radius, data[0]))
        if sorted(allCodes) != sorted(list(tubePos.keys())):
            print(gon[:-4] + " is corrupted and does not have every tube recorded")
            continue
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

        # ************Write analyzed information to a file*************** #
        analyzedFiles.append("\""+gon+"\"" + ": [" + formatTanlineList(rawTanList) + "," + formatTanlineList(paddleTanList)
            + "," + formatTanline(bestTanLine) + "," + formatTanline(bestLine) + "," + str(min(cost.keys())) + "]")

        # ***********************Draw everything********************** #
        eventdraw.drawEvent(imgDir+"\\"+gon[:-4]+".png", tubeHitArray, rawTanList, paddleTanList, cost, bestLine, tubepos=tubePos)

    with open('analyzed.dum', 'w') as f:
        f.write("{")
        writeString = []
        for string in analyzedFiles:
            writeString.append(string)
            writeString.append(", ")
        for string in writeString[:-1]:
            f.write(string)
        f.write("}")
    os.chdir("..")
