from constants import *
from tubehit import *
import numpy as np
import matplotlib.pyplot as plt


# get the x,y positions of each tube in m.  load them into a dict using names as keys
# requires name to be converted from bytes to strings
tubepos = {}
for tube in np.loadtxt("tubepos.csv", delimiter=",", dtype="S3,f4,f4"):
    tubepos[tube[0].decode("utf-8")] = (tube[1], tube[2])

# open data file
with open("sampledata/event1.gon", "r") as file:
    dataArray = []
    # Iterate through every line in the file
    for line in file:
        # takes line, removes the trailing \n, then creates a two element list split at the ;
        data = line[0:-1].split(";")

        # if it's code 256, meaning the tube didn't fire, we don't care
        # otherwise, convert # of clock pulses into radius (m) and xref with the tube x,y pos to make a tubehit event
        if data[1] != "256":
            xy = tubepos[data[0]]
            dataArray.append(tubehit(xy[0], xy[1], float(data[1]) * 1e-8 * DRIFT_VELOCITY, data[0]))

# start the drawing.  draw every tube, then draw every hit
fig, ax = plt.subplots()
for name, pos in tubepos.items():
    ax.add_artist(plt.Circle(pos, OUTER_RADIUS, fill=False, color='r'))
for hit in dataArray:
    ax.add_artist(plt.Circle((hit.x, hit.y), hit.r, fill=False, color='b'))
fig.savefig("name.png")
