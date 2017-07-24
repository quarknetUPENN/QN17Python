from numpy import sqrt, abs, average


# Calculates the distance between any one tubehit and any one tanline
def __distanceFromTubehitToTanline(tubehit, tanline):
    m1 = tanline.m
    b1 = tanline.b
    h = tubehit.x
    k = tubehit.y
    r = tubehit.r

    # an arbitrary expression that is reused in the formula
    D = (h + (k * m1) - (b1 * m1)) / ((m1 ** 2) + 1)

    # the shortest distance between the center of the tubehit and the tanline
    dist = sqrt(((D - h) ** 2) + (((m1 * D) + b1) - k) ** 2)

    # the distance from the tanline to the circle of the tubehit
    # the absolute value penalizes tanlines which are secants of the tubehit circle
    dist = abs(dist - r)
    return dist


# Calculates the cost for any given tanline, given the array of tube hits
# The formula is simply the average of the distances between the tanline and all the tubehits
def tanlineCostCalculator(tanline, tubehitArray):
    cost = [__distanceFromTubehitToTanline(hits, tanline) for hits in tubehitArray]
    return average(cost)
