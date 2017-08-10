from glob import glob

import matplotlib.pyplot as plt
import numpy as np

import circlecalc
from holder import *

tubepos = {}
for tube in np.loadtxt("tubepos.csv", delimiter=",", dtype="S3,f4,f4"):
    tubepos[tube[0].decode("utf-8")] = (tube[1], tube[2])

analyzableEvents = []

os.chdir(rootDataDir)
for dataDir in glob("data_*"):
    # Move to the directory in which the data files are
    os.chdir(dataDir)

    # Iterate through every data file in the directory, generating an output image for them
    for gon in glob("*.gon"):
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
            if len(tubeHitArray) == 4:
                analyzableEvents.append(tubeHitArray)

        if len(tubeHitArray) <= 1:
            print(dataDir[16:] + "," + gon[:-4] + " has no real tubehits")
            continue
    os.chdir("..")
measuredDistance = []
calculatedDistance = []
i = 0
for event in analyzableEvents:
    i += 1
    removedHit = event.pop(int(round(np.random.rand(1)[0]*len(event)))-1)
    rawTanList, paddleTanList, bestTanLine, bestLine, cost = circlecalc.analyzeHits(event, verbose=True)
    if bestLine is None:
        continue
    x0 = removedHit.x
    y0 = removedHit.y
    m = bestLine.m
    b = bestLine.b

    measuredDistance.append(removedHit.r)
    calculatedDistance.append(np.abs(b + m * x0 - y0) / np.sqrt(1 + m ** 2))
    # ***********************Draw everything********************** #
    # create the drawing
    fig, ax = plt.subplots()
    # draw all tubes if requested
    for name, pos in tubepos.items():
        ax.add_artist(plt.Circle(pos, OUTER_RADIUS, fill=False, color='black'))
        ax.text(pos[0], pos[1], name, size=8, ha="center", va="center", alpha=0.5)
    # draw all hit circles if requested
    for hit in event:
        if hit.r <= 3 * 1e-8 * DRIFT_VELOCITY:
            ax.add_artist(plt.Circle((hit.x, hit.y), 3 * 1e-8 * DRIFT_VELOCITY, fill=True, color='red', lw=1.5))
        else:
            ax.add_artist(plt.Circle((hit.x, hit.y), hit.r, fill=False, color='red', lw=1.5))
    hit = removedHit
    ax.add_artist(plt.Circle((hit.x, hit.y), hit.r, fill=False, color='green', lw=1.5))

    ax.plot([PADDLE_MIN_X, PADDLE_MAX_X], [PADDLE_MIN_Y, PADDLE_MIN_Y], color='black', lw=10,
            label="Scintillator Paddle")
    ax.plot([PADDLE_MIN_X, PADDLE_MAX_X], [PADDLE_MAX_Y, PADDLE_MAX_Y], color='black', lw=10)
    # draw the best guess at the particle's track if requested
    lab, = ax.plot([0, 1], [bestLine.y(0), bestLine.y(1)], color="blue", lw=2)
    lab.set_label("Best Line")

    # draw legend to right of graph
    lgd = ax.legend(loc='center left', bbox_to_anchor=(1, 0.5))

    # size the drawing and save it into the imgDir
    ax.set_xlim((0.0, 0.7))
    ax.set_ylim((0.0, 0.7))
    fig.savefig(str(i)+" "+removedHit.tube + ".png", bbox_extra_artists=(lgd,), bbox_inches="tight")
    plt.close(fig)
    print("Saved " +str(i)+" "+removedHit.tube + ".png\n\r")
plt.plot([0,0.015],[0,0.015])
plt.scatter(calculatedDistance, measuredDistance)
plt.savefig("final.png")