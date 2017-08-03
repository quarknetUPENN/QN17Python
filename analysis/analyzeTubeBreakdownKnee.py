from glob import glob

import matplotlib.pyplot as plt
import numpy as np

from holder import *

tubeCodes = []
for tube in loadtxt("tubepos.csv", delimiter=",", dtype="S3,f4,f4"):
    tubeCodes.append(tube[0].decode("utf-8"))

os.chdir("knee1")

voltageData = {}
voltageStd = {}
for dir in glob("data_*V"):
    os.chdir(dir)
    tubeHits = {}
    tubeStd = {}
    for code in tubeCodes:
        tubeHits[code] = []
    gonN = 0
    for gon in glob("*.gon"):
        with open(gon, "r") as file:
            fileData = {}
            # Iterate through every line in the file
            for line in file:
                # takes line, removes the trailing \n, then creates a two element list split at the ;
                data = line[0:-1].split(";")
                fileData[data[0]] = int(data[1])
        if sorted(fileData.keys()) != sorted(tubeCodes):
            print(gon[:-4] + " is corrupted and does not have every tube recorded")
            continue

        for key in fileData.keys():
            tubeHits[key].append(fileData[key])

        gonN += 1

    for key in tubeHits.keys():
        tubeStd[key] = tubeHits[key]
        tubeHits[key] = np.sum(tubeHits[key]) / gonN

    voltageData[int(dir[-5:-1])] = tubeHits
    voltageStd[int(dir[-5:-1])] = tubeStd
    print("Read " + str(gonN) + " gon files for voltage " + str(dir[-5:-1]))
    os.chdir("..")

makeImgDir("kneeImages")
os.chdir("kneeImages")

colors = ['red', 'orange', 'green', 'blue', 'gold', 'purple', 'brown', 'black']

for chamber in ['3', '4']:
    for code in tubeCodes:
        voltages = []
        hits = []
        stds = []
        percentChanceNoise = []
        for voltage in sorted(voltageData.keys()):
            voltages.append(voltage)
            hits.append(voltageData[voltage][code])
            stds.append(voltageStd[voltage][code])
            percentChanceNoise.append(100 * np.average([x < 22 for x in voltageStd[voltage][code]]))

        print(code + str([str(x) for x in zip(voltages, hits)]))

        if code[0] != chamber:
            continue

        if code[1] == 'A':
            ls = "-o"
        else:
            ls = "-s"
        fig, ax = plt.subplots()
        ax.plot(voltages, hits, ls, color='blue', alpha=0.5)  # color=colors[int(code[2])]
        ax1 = ax.twinx()
        ax1.plot(voltages, percentChanceNoise, "-x", color='green')
        ax1.set_ylabel("Percent Chance of Noise Before 220ns")
        ax1.axhline(1, color='red')
        for i in range(len(voltages)):
            ax.scatter(voltages[i] * np.ones(len(stds[i])), stds[i], alpha=10 / len(stds[i]), color='black')

        ax.set_xlabel("Tube Voltage")
        ax.set_ylabel("Average Number of Clock Cycles Before Noise Trigger")
        ax.set_xlim((min(voltageData.keys()), max(voltageData.keys())))

        # lgd = fig.legend(loc='center left', bbox_to_anchor=(1, 0.5))
        plt.title("Breakdown Knee of Tube " + code)
        fig.savefig("tube" + code + ".png")  # , bbox_extra_artists=(lgd,), bbox_inches="tight")
        plt.close(fig)
