from glob import glob
from numpy import loadtxt
import matplotlib.pyplot as plt
from holder import *

tubeCodes = []
for tube in loadtxt("tubepos.csv", delimiter=",", dtype="S3,f4,f4"):
    tubeCodes.append(tube[0].decode("utf-8"))

os.chdir("tubeKneeData")

tubeData = {}
for dir in glob("data_*"):
    os.chdir(dir)
    tubeHits = {}
    for code in tubeCodes:
        tubeHits[code] = 0
    gonN = 0
    for gon in glob("*.gon"):
        gonN += 1
        with open(gon, "r") as file:
            # list to be filled with tubehit events
            tubeHitArray = []
            # Iterate through every line in the file
            for line in file:
                # takes line, removes the trailing \n, then creates a two element list split at the ;
                data = line[0:-1].split(";")
                if not (data[1] == "255"):
                    tubeHits[data[0]] += 1
    for key in tubeHits.keys():
        tubeHits[key] /= gonN * 255 * 10 ** (-8)
    tubeData[int(dir[-5:-1])] = tubeHits
    print("Read " + str(gonN) + " gon files for voltage " + str(dir[-5:-1]))
    os.chdir("..")

makeImgDir("kneeImages")
os.chdir("kneeImages")

for code in tubeCodes:
    voltages = []
    hits = []
    for voltage in sorted(tubeData.keys()):
        voltages.append(voltage)
        hits.append(tubeData[voltage][code])

    print(code + str([str(x) for x in zip(voltages, hits)]))

    plt.scatter(voltages, hits)

    plt.title("Tube " + code + "'s Noise vs Voltage")
    plt.xlabel("Tube Voltage")
    plt.ylabel("Noise Counts per Second")
    plt.xlim((min(tubeData.keys()), max(tubeData.keys())))
    plt.ylim((0, 100000))

    plt.savefig(code + ".png")
    plt.cla()
