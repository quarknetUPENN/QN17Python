from glob import glob
from numpy import loadtxt
import matplotlib.pyplot as plt
from holder import *

tubeCodes = []
for tube in loadtxt("tubepos.csv", delimiter=",", dtype="S3,f4,f4"):
    tubeCodes.append(tube[0].decode("utf-8"))

os.chdir("tubeKneeData")

tubeData = {}
for dir in glob("data_*V"):
    os.chdir(dir)
    tubeHits = {}
    for code in tubeCodes:
        tubeHits[code] = 0
    gonN = 0
    files = ["event"+str(x)+".gon" for x in list(range(32))[1:]]
    for gon in files:
        try:
            with open(gon, "r") as file:
                # list to be filled with tubehit events
                tubeHitArray = []
                # Iterate through every line in the file
                for line in file:
                    # takes line, removes the trailing \n, then creates a two element list split at the ;
                    data = line[0:-1].split(";")
                    tubeHits[data[0]] += int(data[1])
            gonN += 1
        except FileNotFoundError:
            print("rip "+gon)
    for key in tubeHits.keys():
        tubeHits[key] /= gonN

    tubeData[int(dir[-5:-1])] = tubeHits
    print("Read " + str(gonN) + " gon files for voltage " + str(dir[-5:-1]))
    os.chdir("..")

makeImgDir("kneeImages")
os.chdir("kneeImages")

colors = ['red','orange','green','blue','gold','purple','brown','black']

for chamber in ['3','4']:
    for code in tubeCodes:
        voltages = []
        hits = []
        for voltage in sorted(tubeData.keys()):
            voltages.append(voltage)
            hits.append(tubeData[voltage][code])

        print(code + str([str(x) for x in zip(voltages, hits)]))

        if code[0] != chamber:
            continue

        if code[1] == 'A':
            ls = "-o"
        else:
            ls = "-s"
        plt.plot(voltages, hits, ls, label=code, color=colors[int(code[2])])

        plt.xlabel("Tube Voltage")
        plt.ylabel("Average Number of Clock Cycles Before Noise Trigger")
        plt.xlim((min(tubeData.keys()), max(tubeData.keys())))

    lgd = plt.legend(loc='center left', bbox_to_anchor=(1, 0.5))
    plt.title("Breakdown Knees of Chamber "+chamber+"'s Tubes")
    plt.savefig("chamber"+chamber + ".png",bbox_extra_artists=(lgd,), bbox_inches="tight")
    plt.cla()
