# A file to share constants and object frames
import os
from shutil import rmtree

from numpy import linspace, loadtxt

# Constant parameters - standard SI base units (meters, seconds, etc.).
OUTER_RADIUS = 0.0127
WIRE_RADIUS = 0.00005
DRIFT_VELOCITY = 60000
PADDLE_MIN_X = 0.07
PADDLE_MAX_X = 0.341
PADDLE_MIN_Y = 0.075
PADDLE_MAX_Y = 0.652



# Holder class for an event that triggers a tube
class tubeHit:
    def __init__(self, x, y, r, tube):
        # physical x coord of the tube, in m
        self.x = x
        # physical y coord of the tube, in m
        self.y = y
        # physical radius of the triggered event, in m
        self.r = r
        # the code of the tube, eg 3B4
        self.tube = tube

    def toString(self):
        return self.tube + " triggered with a radius of " + str(self.r)


# Holder class for possible tangent lines for particle tracks
class tanLine:
    def __init__(self, m, b):
        # the slope of the line
        self.m = m
        # the y intercept of the line
        self.b = b

    # return the value of the line for a given x coordinate
    def y(self, x):
        return self.m * x + self.b

    # return the value of the x coord for a given y coord
    def x(self, y):
        if (self.m == 0):
            print("Warning: Attempted to find x value for a given y value of horizontal line.  Returning 0")
            return 0
        return (y - self.b) / self.m

    def toString(self):
        return "slope: " + str(self.m) + " intercept: " + str(self.b)


# Holder class to define the area over which a certain parameter should be scanned
class scanParam:
    def __init__(self, width, n, enable):
        # the area to scan over; that is, +- this width from the central value
        self.width = width
        # the number of points to scan over
        self.n = n

        if type(enable) != bool:
            raise TypeError("Enable of a scanParam should be a boolean, instead was: " + str(enable))

        # whether or not to scan over this parameter
        self.enable = enable

    # given the center value, returns a list of points to scan over
    def range(self, param):
        if self.enable:
            return linspace(param - self.width, param + self.width, num=self.n)
        else:
            return [param]

# define what to plot
plotConfig = {"showTubes": True,
              "showTubeLabels": True,
              "showPaddles": True,
              "showHitCircles": True,
              "showAllPossibleTanLines": False,
              "showPaddleTanLines": False,
              "showSearchedLines": False,
              "showBestLine": True}
# define what spread and how many points to iterate around the best tanline for various attributes
scanParams = {"m": scanParam(0.2, 10, True),
              "x": scanParam(0.01, 10, True),
              "y": scanParam(0.005, 10, True)}
# ignore these tubes, pretend they never fire
tubeBlacklist = ["3B3"]
# the directory that has the timestamped data folders in it
rootDataDir = "runs/"

# Make a directory for images, at all costs, recursively
def makeImgDir(dir):
    # make sure the input is what we think it should be
    dir = str(dir)
    # if the directory exists, then we have to decide what to do.  if it doesn't, make the directory
    if os.path.isdir(dir):
        # ask the user whether or not they want to overwrite the current directory.  if they want to, then kill
        # and remake the directory.  otherwise, procedurally generate a new image directory name, and try that
        if str(input("Existing image directory \"" + os.getcwd() + "\\"+dir + "\" found.  " +
                             "Burn it with fire and bury the body? (y/n): ")) == "y":
            rmtree(dir)
            os.makedirs(dir)
            return dir
        else:
            return makeImgDir("new" + dir)
    else:
        os.makedirs(dir)
        return dir

# ******************Load tube position data***************** #
def loadTubePos():
    # using numpy, get the x,y positions of each tube in m.  load them into a dict using names as keys
    # requires name to be converted from bytes to strings
    tubepos = {}
    for tube in loadtxt("tubepos.csv", delimiter=",", dtype="S3,f4,f4"):
        tubepos[tube[0].decode("utf-8")] = (tube[1], tube[2])
    return tubepos