# The main script.  Run this script to analyze a folder of .gon event files into .png files and a .dum file
from glob import glob

import circlecalc
import eventdraw
from holder import *

# subfolder name in which to put the images (will be generated as a subfolder of dataDir).  If it already exists,
# we'll try to make a different one
imgDir = "images"


# given a list of tanLine objects, format all of them as tanLine constructors as strings
# then put them all into a list and surround with [] to make it a list of tanLine constructors...all as a string
# this is for writing to the .dum files.  it will eventually be passed to exec() to make a real Python list
def formatTanlineList(tanlineList):
    output = "["
    for line in tanlineList:
        output += formatTanline(line) + ","
    # remove the trailing comma and add the end bracket
    return output[:-1] + "]"


# given a tanLine object, formats it into a tanLine constructor as a string
# this is eventually passed to exec() to create a real object
def formatTanline(tanline):
    return "tanLine(" + str(tanline.m) + "," + str(tanline.b) + ")"


# ******************Load tube position data***************** #
# using numpy, get the x,y positions of each tube in m.  load them into a dict using names as keys
# requires name to be converted from bytes to strings
tubePos = loadTubePos()

os.chdir(rootDataDir)

for dir in glob("data_2017-*"):
    os.chdir(dir)
    # a list to be filled with the intermediates of the particle track calculation; this will eventually be written to a .dum file
    analyzedFiles = []
    # Make the image directory, even if it's not exactly the specified one.  it gets filled with images eventually
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
        # check to make sure that every tube code that should have appeared, did indeed appear
        # not sure if sorting is needed here.  doesn't hurt though
        if sorted(allCodes) != sorted(list(tubePos.keys())):
            print(gon[:-4] + " is corrupted and does not have every tube recorded")
            continue
        # check to make sure that there are enough tube hits to analyze
        if len(tubeHitArray) <= 1:
            print(gon[:-4] + " has no real tubehits, skipping")
            continue

        # **********************Analyze event data********************** #
        results = circlecalc.analyzeHits(tubeHitArray, verbose=True)
        # check to make sure that the analysis actually ran.  if it didn't run, it means that all the tangent lines were invalid
        # that is, none of them passed through scintillator paddles
        if results[-1] is None:
            print(gon[:-4] + " has no valid tanlines, skipping")
            continue
        else:
            rawTanList, paddleTanList, bestTanLine, bestLine, cost = results

        # *****************Save analyzed information******************** #
        analyzedFiles.append(
            "\"" + gon + "\"" + ": [" + formatTanlineList(rawTanList) + "," + formatTanlineList(paddleTanList)
            + "," + formatTanline(bestTanLine) + "," + formatTanline(bestLine) + "," + str(min(cost.keys())) + "]")

        # ***********************Draw everything********************** #
        eventdraw.drawEvent(imgDir + "\\" + gon[:-4] + ".png", tubeHitArray, rawTanList, paddleTanList, cost, bestLine,
                            tubepos=tubePos)

    # *****************Write analyzed information to a file******************** #
    with open('analyzed.dum', 'w') as f:
        # open the dictionary
        f.write("{")

        # every single element of analyzedFiles is a Python dictionary entry.  they just need to be combined
        # therefore, append each with a , and a space between each to make the internals of the dictionary
        # this does, however, leave a trailing ", " combo
        writeString = []
        for string in analyzedFiles:
            writeString.append(string)
            writeString.append(", ")

        # remove the last element of writeString, because it is a trailing ", ".  write everything else sequentially
        for string in writeString[:-1]:
            f.write(string)

        # close the dictionary
        f.write("}")
    os.chdir("..")
