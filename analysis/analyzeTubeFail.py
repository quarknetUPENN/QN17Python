from glob import glob

import matplotlib.pyplot as plt
import numpy as np

from analysis import outputFolder
from holder import *

# these dictionaries are used to easily convert between coordinates and tube names wherever is needed
# a dictionary mapping the tube name to a tuple (x,y) of its physical location in x and y
tubepos = {}
# a dictionary that's the reverse of tubepos - mapping the tuple (x,y) of its physical location to the tube name
reverseTubePos = {}

# these lists are used to calculate the minimum distances between each tube hit that should have occurred and the lines
# a list of all the possible x coordinates for the set of tubes on layer A
tubeaxs = []
# a list of all the possible x coordinates for the set of tubes on layer B
tubebxs = []
# a list of all the possible y coordinates for all tubes
tubeys = []

# these two dictionaries are used directly to generate the tube fail rate vs tube name
# a dictionary that maps the tube name to the number of times it fails to fire when it should
tubeFailFreq = {}
# a dictionary that maps the tube name to the number of times it fires when it should
tubeNotFailFreq = {}

# a dictionary that maps tube names to another dictionary that maps the radius in clock cycles to the number of failed events at that radius
# this is later used to generate the heatmaps, because it correlates both tube name and radius to failed events
tubeAndRadius = {}

# fill all those variables above
for tube in loadtxt("tubepos.csv", delimiter=",", dtype="S3,f4,f4"):
    tubepos[tube[0].decode("utf-8")] = (tube[1], tube[2])
    reverseTubePos[(round(tube[1], 4), round(tube[2], 4))] = tube[0].decode("utf-8")
    tubeFailFreq[tube[0].decode("utf-8")] = 0
    tubeNotFailFreq[tube[0].decode("utf-8")] = 0
    tubeAndRadius[tube[0].decode("utf-8")] = {}
    if tube[0].decode("utf-8")[1] == 'A':
        tubeaxs.append(tube[1])
    else:
        tubebxs.append(tube[1])
    tubeys.append(tube[2])

# remove any duplicates from the tube x and y coordinates.  sorting is just for readability
tubeaxs = sorted(list(set(tubeaxs)))
tubebxs = sorted(list(set(tubebxs)))
tubeys = sorted(list(set(tubeys)))

# a list to be filled with every single tubeHit recorded from all the searched gon files
allTubeHits = []

# a list to be filled with the radii of a tube hits that should have occurred but didn't
# this is later used to help generate the tube fail rate vs tube radius
minxdists = []

# Move to the directory in which the data folders are
os.chdir(rootDataDir)

# **********************Load event data********************** #
# go through every data folder
for dir in glob("data_2017-*"):
    # go into the data folder for convenience
    os.chdir(dir)

    # load the analyzed data from the .dum file
    # the file should only have one line.  exec() will interpret the file as real python code
    # this is a security vulnerability if anyone ever cares, since there is no sanitation of the .dum file text
    analyzed = {}
    with open('analyzed.dum', 'r') as file:
        exec("analyzed = " + file.readline())

    # Iterate through every data file in the directory, processing them
    for gon in glob("*.gon"):
        with open(gon, "r") as file:
            # list to be filled with tubeHits for each gon file
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
            print(dir + "\\" + gon[:-4] + " has no real tubehits, skipping")
            continue

        # **********************Get analyzed event data********************** #
        # this finds the analyzed data from the dictionary that came from the .dum file and pulls the information
        # however, if the dum file doesn't have this event, it means that the event had no valid tanlines
        # and therefore did not make an entry for it
        try:
            rawTanList, paddleTanList, bestTanLine, bestLine, cost = analyzed[gon]
        except KeyError:
            print(dir + "\\" + gon[:-4] + " has no valid tanlines, skipping")
            continue

        # ******************Find the tube failure events********************** #
        # go through the event y-layer by y-layer.  A track, ideally, will leave one hit on each y-layer
        # if there was a hit on that layer, see if it was a good hit.  Mark as failed or not failed
        # if there was not a hit on that layer, figure out where it should have been.  Mark as failed
        # a counter variable to keep track of whether we are on layer a or b as we go through y (even numbers indicate A, odd numbers are B)
        i = 0
        for y in tubeys:
            i += 1

            # if we recorded a hit on this layer, go figure out which hit it from tubeHitArray
            # if the tangent line actually passed through the tube, then mark it down that this tube worked
            # if the tangent line did not pass through teh tube, then mark down that this tube failed
            if y in [tubehit.y for tubehit in tubeHitArray]:
                for tubehit in tubeHitArray:
                    if y == tubehit.y:
                        if np.abs(tubehit.x - bestLine.x(y)) <= OUTER_RADIUS:
                            tubeNotFailFreq[tubehit.tube] += 1
                        else:
                            tubeFailFreq[tubehit.tube] += 1
                continue

            # --if we did not have a hit on this layer, figure out where we should have had a hit-- #

            # first, figure out what all the x coordinates of the tubes on this level are
            # modulo of i will tell us if we are on level A or B, which gives the X coordinates
            tubexs = []
            if i % 2 == 0:
                tubexs = tubeaxs
            else:
                tubexs = tubebxs

            # since we didn't record a hit on this layer and we should've, figure out what the radius should have been
            # this dictionary will map [the distance from the center of the tube to the particle track] to the X coordinate of the tube
            # for every tube on this level
            xdists = {}
            # fill xdists by going through every tube on the layer, and record the distance between the line and each tube
            for x in tubexs:
                m = bestLine.m
                b = bestLine.b
                xdists[(np.abs(b + m * x - y) / np.sqrt(1 + m ** 2))] = x

            # occasionally, the track passes outside of the tubes.  log this and then ignore it
            # this could happen with two tube hits recorded on the edge of the same chamber (ie, 3A0 & 3B0)
            # the line would still pass through the scintillator paddles because we had them drawn too large
            # we didn't know that at the time.  this should be useless now, but it covers an edge case
            if min(xdists.keys()) > OUTER_RADIUS:
                print(dir + gon + " has a track that does not pass through 4 tubes?")
                continue

            # record the closest distance between any tube on this layer and the spot where the line passed through this layer
            minxdists.append(min(xdists.keys()))

            # look up the tube from its x,y coordinates, and mark that it failed
            tubeFailFreq[reverseTubePos[(xdists[min(xdists.keys())], y)]] += 1
        print("Processed " + dir + "\\" + gon[:-4])
    os.chdir("..")
os.chdir("..")

# ------------------------------------------------------- #
# **********************Draw graphs********************** #
# ------------------------------------------------------- #

# ***************heatmap of hits vs tube code and radius*************** #
# fill up every dictionary in tubeAndRadius with 0s for all possible radii
# this is the fastest way to initialize tubeAndRadius.  the actual values are later put in by adding to the existing number
# if there is no existing number, than an error will be thrown.  This ensures that all the numbers that should be there are there
for key in tubeAndRadius:
    for n in range(23):
        tubeAndRadius[key][n] = 0
# now, fill tubeAndRadius with actual data.  Take allTubeHits and parse it into the format for tubeAndRadius
for tubehit in allTubeHits:
    tubeAndRadius[tubehit.tube][round(tubehit.r / (DRIFT_VELOCITY * 10 ** (-8)))] += 1

# then, use black magic to parse tubeAndRadius into the heatmap.  I hope you like list comprehensions and gymnastics
# image will eventually be a Python 2D array - that is, a list of lists - that is shown in the output figure
# this means its vertical axis is tube code, its horizontal axis is radius, and the values are the number of recorded hits
# first, we make it a list for every key in tubeAndRadius - that is, all the tube names - and then we go through, and replace
# every tube name with a list of that tube's hits across radius.  thus, this 1D list gets 'expanded' into a 2D image
# note that there are no labels on this array; it's JUST the image.  In order to keep track of the order it's in, we
# sort the tube names.  we don't explicitly carry the order the tube names are in; it's implicitly known to be alphabetical
image = [str(x) for x in sorted(tubeAndRadius.keys())]
for tube in image:
    image[image.index(tube)] = [tubeAndRadius[tube][rad] for rad in sorted(tubeAndRadius[tube].keys())]

# now, add a line to the top of the image.  this is the sum of all the hits, so you can see an overall distribution
# we use np.sum to add everything in one dimension, collapsing the 2D image into a 1D list of the number of hits at each
# radius, independent of tube code.  we divide this elementwise by the number of tubes - 32 - in order to keep all the
# numbers on the same magnitude
image.append(list(np.divide(np.sum(image, axis=0), 32)))

# this actually draws the heatmap as grayscale.  Normalization is done for us
plt.imshow(np.array(image), cmap=plt.get_cmap("Greys"), interpolation="none", aspect="equal")

# this probably shows my horrible lack of knowledge of matplotlib, but it works
# it figures out the implicit order of the tubes in the image.  then, it draws a blank & transparent horizontal bar graph
# with those labels, to show just the labels
labels = sorted(tubeAndRadius.keys())
labels.append("SUM")
plt.barh(np.arange(0, 33, step=1), np.zeros(33), alpha=0, tick_label=labels)

# this makes the scale on the right side of the graph
plt.colorbar()

# frame the image properly - the +-0.5 is because imshow draws each pixel centered over its value
# also label it, save it, and delete it from RAM
plt.xlim((-0.5, 22.5))
plt.ylim((-0.5, 32.5))
plt.xlabel("Radius in Number of Clock Cycles")
plt.title("Number of Events for Tube at Radius")
plt.savefig(outputFolder + "TubeHitRadiusCode.png")
plt.cla()
plt.clf()

# ***************Tube Fails Versus Hit Radius*************** #
# draw the number of recorded tube hits and the number of missed tube hits vs radius of the hit
# this looks across all tubes and looks at the sensitivity of the tube close in and far out
# ideally, the missed tube hits would all be 0
# this also uses some weird comprehensions to parse minxdists.  But, all it's doing is converting minxdists from meters
# to clock cycles, and then putting it in a histogram
(n, bins, patches) = plt.hist([round(x / (DRIFT_VELOCITY * 10 ** (-8))) for x in minxdists],
                              bins=round(max(minxdists) / (DRIFT_VELOCITY * 10 ** (-8))), label="Missed Tube Hits")
# do the same thing but with the actual tube hits
plt.hist([round(tubehit.r / (DRIFT_VELOCITY * 10 ** (-8))) for tubehit in allTubeHits], bins=bins, alpha=0.5,
         color='red', label="Recorded Tube Hits")

# title, label, size, add a legend, save, delete from RAM
plt.xlabel("Radius in Clock Cycles")
plt.ylabel("Number of Events Recorded")
plt.title("Tube Fail Rate vs Hit Radius")
plt.xlim((0, 25))
plt.legend()
plt.savefig(outputFolder + "TubeFailRateRadius.png")
plt.cla()

# ***************Tube Fails Versus Tube Code*************** #
# draw the fraction of hits missed for each tube
# ideally, everything is 0.  this tells you how a given tube is performing

# Parse all the data from tubeFailFreq.  Basically, write it out as a couple lists, all in the same order of tubes
# note: everything except tubeList and percentList are no longer used.  We used to use them,  and never saw a reason to remove them
# a list to be filled with all the tube codes in order
tubeList = []
# a list to be filled with the failure rates for those tube codes, in the same order as tubeList
failList = []
# a list to be filled with the good hit rates for tubeList's tube codes, in the same order
notFailList = []
# a list to be filled with a decimal number representing the fraction of the time the tube fails to hit out of all its hits
# this is in the same order as tubeList
percentList = []

# go through and actually fill those lists, in alphabetical order
for key in sorted(tubeFailFreq.keys()):
    # if the tube is blacklisted, just put a bunch of 0s in to denote that
    if key in tubeBlacklist:
        tubeList.append(key)
        failList.append(0)
        notFailList.append(0)
        percentList.append(0)
        continue
    tubeList.append(key)
    failList.append(tubeFailFreq[key])
    notFailList.append(tubeNotFailFreq[key])
    percentList.append(tubeFailFreq[key] / (tubeFailFreq[key] + tubeNotFailFreq[key]))

# draw that parsed data as a horizontal bar
plt.barh(np.arange(len(tubeFailFreq)), percentList, tick_label=tubeList)

# title, labels, save, etc
plt.xlabel("Fraction of Missed Events")
plt.ylabel("Tube Code")
plt.title("Tube Fail Rate vs Tube Code")
plt.savefig(outputFolder + "TubeFailRateCode.png")
