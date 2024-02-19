import os

os.environ["XDG_SESSION_TYPE"] = "xcb"


def drawLine(arr):
    import matplotlib.pyplot as plt
    ax = plt.figure().add_subplot(projection='3d')
    for item in arr:
        plt.plot(item[0], item[1], item[2])
    ax.set_xlabel('x')
    ax.set_ylabel('y')
    ax.set_zlabel('z')

    ax.set_xlim(-15, 15)
    ax.set_ylim(-15, 15)
    ax.set_zlim(-1, 15)

    plt.show()
