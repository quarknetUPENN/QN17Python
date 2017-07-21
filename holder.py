# A file to share constants and object frames
# Constant parameters - standard SI base units (meters, seconds, etc.).
OUTER_RADIUS = 0.0127
WIRE_RADIUS = 0.00005
DRIFT_VELOCITY = 60000
PADDLE_MIN_X = 0.07
PADDLE_MAX_X = 0.3
PADDLE_MIN_Y = 0
PADDLE_MAX_Y = 0.5

# Holder class for an event that triggers a tube
class tubehit:
    def __init__(self, x, y, r, tube):
        # physical x coord of the tube, in m
        self.x = x
        # physical y coord of the tube, in m
        self.y = y
        # physical radius of the triggered event, in m
        self.r = r
        # the code of the tube, eg 3B4
        self.tube = tube

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
        return (y-self.b)/self.m

    def toString(self):
        return "slope: " + str(self.m) + " intercept: " + str(self.b)