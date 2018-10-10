import operator

import matplotlib.pyplot as plt


def plot(cities, path: list):
    x = []
    y = []
    fig, ax = plt.subplots()

    for city in cities:
        p_y = city[0]
        p_x = city[1]
        p_name = city[2]

        x.append(p_x)
        y.append(p_y)
        plt.plot(p_x, p_y, 'bo')

        ax.annotate(p_name, (p_x+0.05, p_y+0.05))

    for local_p in range(1, len(path)):
        i = path[local_p - 1]
        j = path[local_p]
        plt.arrow(x[i], y[i], x[j] - x[i], y[j] - y[i], color='r', length_includes_head=True)

    plt.show()
