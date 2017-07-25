# A file to hold functions relating to calculations on the circles
from numpy import sqrt

from holder import *


# utilizes primordial black magic from 2016 to solve for the 4 possible tangent lines, given two tubehit objects
# returns a list of tanLine objects
def possibleTan(tubehit1, tubehit2):
    # list to be filled with tanLine objects representing possible tan lines
    tanList = []
    # create lists describing h,k,r for each circle
    x = [tubehit1.x, tubehit2.x]
    y = [tubehit1.y, tubehit2.y]
    r = [tubehit1.r, tubehit2.r]
    if r[1] * x[0] == r[0] * x[1]:
        print("x:" + str(x))
        print("y:" + str(y))
        print("r:" + str(r))
        print(tubehit1.tube)
        print(tubehit2.tube)

    # i,j both can be +1 or -1, so are effectively +-s.  Makes sense - 4 combos for 4 possible tan lines
    for i in range(-1, 2, 2):
        for j in range(-1, 2, 2):
            if (r[1] * x[0] == r[0] * x[1]) and i == -1:
                print("ignoring vertical tan line on " + tubehit1.tube + " and " + tubehit2.tube)
                break
            # shared coefs for the quadratic
            Q = (r[1] * y[0] + i * r[0] * y[1]) / (r[1] * x[0] + i * r[0] * x[1])
            P = (r[1] + i * r[0]) / (r[1] * x[0] + i * r[0] * x[1])

            # quadratic coefs
            a = Q ** 2 * x[0] ** 2 - 2 * Q * x[0] * y[0] + y[0] ** 2 - Q ** 2 * r[0] ** 2 - r[0] ** 2
            b = 2 * Q * P * x[0] ** 2 - 2 * Q * x[0] - 2 * P * x[0] * y[0] + 2 * y[0] - 2 * Q * P * r[0] ** 2
            c = P ** 2 * x[0] ** 2 - 2 * P * x[0] - P ** 2 * r[0] ** 2 + 1

            # solve the quadratic, and calculate m,b for y=mx+b tan lines
            if b ** 2 - 4 * a * c >= 0:
                soln = (-b + j * sqrt(b ** 2 - 4 * a * c)) / (2 * a)
                slope = Q + (P/soln)
                intercept = -1/soln

                tanList.append(tanLine(slope, intercept))
    return tanList

# given a list of tanLines, removes all of those that don't pass through both paddles
# returns this new list of tanLines
def removeSideTanLines(tanList):
    newList = []
    for line in tanList:
        if line.m != 0:
            if not (line.x(PADDLE_MAX_Y) > PADDLE_MAX_X or line.x(PADDLE_MAX_Y) < PADDLE_MIN_X or
                            line.x(PADDLE_MIN_Y) > PADDLE_MAX_X or line.x(PADDLE_MIN_Y) < PADDLE_MIN_X):
                newList.append(line)
    return newList
