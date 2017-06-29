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
    ax.add_artist(plt.Circle(pos, OUTER_RADIUS, fill=False, color='black'))
for hit in dataArray:
    ax.add_artist(plt.Circle((hit.x, hit.y), hit.r, fill=False, color='blue'))


# choose two hits out of the array to draw the 4 possible tan lines for, and draw those circles in red
index1 = 2
index2 = 3
ax.add_artist(plt.Circle((dataArray[index1].x, dataArray[index1].y), dataArray[index1].r, fill=False, color='r'))
ax.add_artist(plt.Circle((dataArray[index2].x, dataArray[index2].y), dataArray[index2].r, fill=False, color='r'))

# primordial black magic from 2016 that solves for the 4 possible tangent lines
# create lists describing h,k,r for each circle
x = [dataArray[index1].x, dataArray[index2].x]
y = [dataArray[index1].y, dataArray[index2].y]
r = [dataArray[index1].r, dataArray[index2].r]
# i,j both can be +1 or -1, so are effectively +-s.  Makes sense - 4 combos for 4 possible tan lines
for i in range(-1, 2, 2):
    for j in range(-1, 2, 2):
        # shared coefs for the quadratic
        Q = (r[1] * y[0] + i * r[0] * y[1]) / (r[1] * x[0] + i * r[0] * x[1])
        P = (r[1] + i * r[0]) / (r[1] * x[0] + i * r[0] * x[1])

        # quadratic coefs
        a = Q ** 2 * x[0] ** 2 - 2 * Q * x[0] * y[0] + y[0] ** 2 - Q ** 2 * r[0] ** 2 - r[0] ** 2
        b = 2 * Q * P * x[0] ** 2 - 2 * Q * x[0] - 2 * P * x[0] * y[0] + 2 * y[0] - 2 * Q * P * r[0] ** 2
        c = P ** 2 * x[0] ** 2 - 2 * P * x[0] - P ** 2 * r[0] ** 2 + 1

        # solve the quadratic, and draw the lines in green
        if b ** 2 - 4 * a * c >= 0:
            soln = (-b + j * np.sqrt(b ** 2 - 4 * a * c)) / (2 * a)
            slope = Q + (P/soln)
            intercept = -1/soln
            plt.plot([0, 1], [intercept, slope+intercept], color='green')

# size the plot and save it
plt.xlim((0,0.5))
plt.ylim((0,0.5))
fig.savefig("name.png")
