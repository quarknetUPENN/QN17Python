from numpy import sqrt


def __distanceFromTubehitToTanline(tubehit, tanline):
    m1 = tanline.m
    b1 = tanline.b
    h = tubehit.x
    k = tubehit.y
    r = tubehit.r

    D = (h + (k * m1) - (b1 * m1)) / ((m1 ** 2) + 1)
    dist = sqrt(((D - h) ** 2) + (((m1 * D) + b1) - k) ** 2)
    dist = dist - r
    if dist < 0:
        dist = 0
    return dist


def tanlineCostCalculator(tanline, tubehitArray):
    cost = 0
    for hits in tubehitArray:
        cost += __distanceFromTubehitToTanline(hits, tanline)

        #print("Cost: " + str(cost))
    return cost