# The main script.  Run this script to analyze a folder of .gon event files
from holder import *
import circlecalc as cc
import matplotlib.pyplot as plt
from numpy import loadtxt
from glob import glob
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler
import numpy as np
import os
import tanlineoptimizer as tlo


def __histogramPeakFinder(data):
    (n,bins, patches) = plt.hist(data)
    n = np.array(n)
    print(n)
    binedge = bins[np.argmax(n)]
    print("Left bin edge: " + str(binedge))
    binwidth = (max(m)-min(m))/plt.rcParams["hist.bins"]
    print("Binwidth: " + str(binwidth))
    print("Right bin edge: " + str(binedge + binwidth))
    return [binedge, binedge + binwidth]



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
              "showAverageTanLine": False}

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
        dataArray = []
        # Iterate through every line in the file
        for line in file:
            # takes line, removes the trailing \n, then creates a two element list split at the ;
            data = line[0:-1].split(";")

            # if it's code 256, meaning the tube didn't fire, ignore it, we don't care
            # otherwise convert # of clock pulses into radius (m) and xref with the tube x,y pos to make a tubehit event
            if data[1] != "256":
                xy = tubepos[data[0]]
                dataArray.append(tubehit(xy[0], xy[1], float(data[1]) * 1e-8 * DRIFT_VELOCITY, data[0]))

    # ******************Find possible tan lines******************* #
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
        for hit in dataArray:
            ax.add_artist(plt.Circle((hit.x, hit.y), hit.r, fill=False, color='blue'))
    # draw both paddles if requested
    if plotConfig["showPaddles"]:
        ax.plot([PADDLE_MIN_X, PADDLE_MAX_X], [PADDLE_MIN_Y, PADDLE_MIN_Y], color='black', lw=10, label="Scintillator Paddle")
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
    # draw average tan line if requested
    if plotConfig["showAverageTanLine"]:
        lab, = ax.plot([0, 1], [avgLine.y(0), avgLine.y(1)], color="red", ls="-", lw=2)
        lab.set_label("Average Tangent Line")
    # draw legend to right of graph
    lgd = ax.legend(loc='center left', bbox_to_anchor=(1, 0.5))



    # size the drawing and save it into the imgDir
    plt.xlim((0, 0.5))
    plt.ylim((0, 0.5))


    m = []
    b = []
    for line in paddleTanList:
        m.append(line.m)
        b.append(line.b)
    print(len(m))
    print(len(b))
    #print(m)
    #print(b)


    # print(__distanceFromTubehitToTanline(dataArray[0], tanLine(3,2)))
    # print(__tanlineCostCalculator(tanLine(3,2), dataArray))

    cost = {}
    mrange = __histogramPeakFinder(m)
    brange = __histogramPeakFinder(b)
    for m2 in np.arange(mrange[0], mrange[1]):
        for b2 in np.arange(brange[0], brange[1]):
            cost[tlo.tanlineCostCalculator(tanLine(m2,b2), dataArray)] = tanLine(m2,b2)
    # for line in cost.values():
    #     print(line.toString())

    print(cost[min(cost.keys())].toString())
    bestline =  (cost[min(cost.keys())])

    ax.plot([0,1], [bestline.y(0), bestline.y(1)], color = "b", lw = "3")

    fig.savefig(imgDir+"/"+gon[:-4]+".png", bbox_extra_artists=(lgd,), bbox_inches="tight")

    fig, ax = plt.subplots()
    ax.scatter(m, b, marker=".")
    #ax.set_xlim((-190,-180))
    #ax.set_ylim((40,50))
    fig.savefig(imgDir+"/"+gon[:-4]+"bVm"+".png")
    fig, ax = plt.subplots()
    ax.hist(m)
    fig.savefig(imgDir+"/"+gon[:-4]+"mhist"+".png")
    fig, ax = plt.subplots()
    ax.hist(b)
    fig.savefig(imgDir+"/"+gon[:-4]+"bhist"+".png")




    # #implementing DBSCAN(based on 2016 parameters)
    # db = DBSCAN(eps=0.8, min_samples = 5).fit(array)
    # core_samples_mask = np.zeros_like(db.labels_, dtype=bool)
    # core_samples_mask[db.core_sample_indices_] = True
    # labels = db.labels_
    # #returns the number of clusters given by DBSCAN
    # n_clusters= len(set(labels)) - (1 if -1 in labels else 0)
    # print(n_clusters)
    #
    #
    # unique_labels = set(labels)
    # colors = [plt.cm.Spectral(each)
    #           for each in np.linspace(0, 1, len(unique_labels))]
    # for k, col in zip(unique_labels, colors):
    #     if k == -1:
    #         # Black used for noise.
    #         col = 'k'
    #
    #     class_member_mask = (labels == k)
    #
    #
    #
    # xy = array[class_member_mask & core_samples_mask]
    # plt.plot(xy[:, 0], xy[:, 1], 'o', markerfacecolor= col, markeredgecolor='k', markersize=14)
    #
    # xy = array[class_member_mask & ~core_samples_mask]
    # plt.plot(xy[:, 0], xy[:, 1], 'o', markerfacecolor= col , markeredgecolor='k', markersize=6)
    #
    # #plt.title('Estimated number of clusters: %d' % n_clusters)
    # plt.show()
    #
    # #plt.savefig(imgDir+"/"+gon[:-4]+"dbscan1"+".png")
