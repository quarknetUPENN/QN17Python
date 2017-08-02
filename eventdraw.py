from holder import *
import matplotlib.pyplot as plt


def drawEvent(saveName, tubeHitArray=None, rawTanList=None, paddleTanList=None, cost=None, bestLine=None,
              plotConfiguration=None, tubepos=None):
    if tubepos is None:
        tubepos = loadTubePos()
    if plotConfiguration is None:
        plotConfiguration = plotConfig

    # create the drawing
    fig, ax = plt.subplots()
    # draw all tubes if requested
    if plotConfiguration["showTubes"]:
        for name, pos in tubepos.items():
            ax.add_artist(plt.Circle(pos, OUTER_RADIUS, fill=False, color='black'))
            if plotConfiguration["showTubeLabels"]:
                ax.text(pos[0], pos[1], name, size=8, ha="center", va="center", alpha=0.5)

    # draw all hit circles if requested
    if plotConfiguration["showHitCircles"]:
        if tubeHitArray is None:
            print(
                saveName + "'s tubeHitArray was not specified, but plotConfiguration showHitCircles is true.  Ignoring")
        else:
            for hit in tubeHitArray:
                if hit.r <= 3 * 1e-8 * DRIFT_VELOCITY:
                    ax.add_artist(plt.Circle((hit.x, hit.y), 3 * 1e-8 * DRIFT_VELOCITY, fill=True, color='red', lw=1.5))
                else:
                    ax.add_artist(plt.Circle((hit.x, hit.y), hit.r, fill=False, color='red', lw=1.5))

    # draw both paddles if requested
    if plotConfiguration["showPaddles"]:
        ax.plot([PADDLE_MIN_X, PADDLE_MAX_X], [PADDLE_MIN_Y, PADDLE_MIN_Y], color='black', lw=10,
                label="Scintillator Paddle")
        ax.plot([PADDLE_MIN_X, PADDLE_MAX_X], [PADDLE_MAX_Y, PADDLE_MAX_Y], color='black', lw=10)

    # draw all possible tan lines if requested
    if plotConfiguration["showAllPossibleTanLines"]:
        if rawTanList is None:
            print(
                saveName + "'s rawTanList was not specified, but plotConfiguration showAllPossibleTanLines is true.  Ignoring")
        else:
            for line in rawTanList:
                lab, = ax.plot([0, 1], [line.y(0), line.y(1)], color="green", ls="--", lw=0.5)
            lab.set_label("All Tangent Lines")

    # draw all tan lines through paddle if requested
    if plotConfiguration["showPaddleTanLines"]:
        if paddleTanList is None:
            print(
                saveName + "'s paddleTanList was not specified, but plotConfiguration showPaddleTanLines is true.  Ignoring")
        else:
            for line in paddleTanList:
                lab, = ax.plot([0, 1], [line.y(0), line.y(1)], color="green", ls="-", lw=1)
            lab.set_label("Paddle Tangent Lines")

    # draw all the lines that were searched around the tan line
    if plotConfiguration["showSearchedLines"]:
        if cost is None:
            print(
                saveName + "'s cost dictionary was not specified, but plotConfiguration showSearchedLines is true.  Ignoring")
        else:
            for line in cost.values():
                lab, = ax.plot([0, 1], [line.y(0), line.y(1)], color="yellow", lw=0.01)
            lab.set_label("Searched Lines")

    # draw the best guess at the particle's track if requested
    if plotConfiguration["showBestLine"]:
        if bestLine is None:
            print(saveName + "'s bestLine was not specified, but plotConfiguration showBestLine is true.  Ignoring")
        else:
            lab, = ax.plot([0, 1], [bestLine.y(0), bestLine.y(1)], color="blue", lw=2)
            lab.set_label("Best Line")

    # draw legend to right of graph
    lgd = ax.legend(loc='center left', bbox_to_anchor=(1, 0.5))

    # size the drawing and save it into the imgDir
    ax.set_xlim((0.0, 0.7))
    ax.set_ylim((0.0, 0.7))
    fig.savefig(saveName, bbox_extra_artists=(lgd,), bbox_inches="tight")
    plt.close(fig)
    print("Saved " + os.getcwd() + "\\" + saveName + "\n\r")
