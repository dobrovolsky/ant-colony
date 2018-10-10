import json

from aco import (
    ACO,
    Graph,
)
from plot import plot
from prepare_data import (
    Downloader,
    DistanceMatrix,
)


def main():
    cities = []
    cost_matrix = []

    with open('./LV_DISTANCE.json') as f:
        data = json.load(f)

    for k, v in data.items():
        x, y = v['point']
        cities.append((y, x, k))
        cost_matrix.append([city['distance'] for city in v['cities']])

    aco = ACO(100, 10, 1, 10.0, 0.5, 10, 2)
    graph = Graph(cost_matrix, len(data))
    path, cost = aco.solve(graph)
    print('cost: {}, path: {}'.format(cost, path))
    plot(cities, path)


if __name__ == '__main__':
    Downloader().download()
    dm = DistanceMatrix()
    dm.init_cities()
    dm.init_matrix()

    main()
