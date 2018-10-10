import json

import settings
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

    with open(settings.CITIES_DISTANCE) as f:
        data = json.load(f)

    for k, v in data.items():
        x, y = v['point']
        cities.append((y, x, k))
        cost_matrix.append([city['distance'] for city in v['cities']])

    aco = ACO(
        ant_count=20,
        run_without_improvement=20,
        alpha=2,
        beta=5,
        rho=0.5,
        q=5,
        pheromone_strategy='ant_density')

    graph = Graph(cost_matrix)
    path, cost = aco.solve(graph)
    print('cost: {}, path: {}'.format(cost, path))
    plot(cities, path)


if __name__ == '__main__':
    Downloader().download()
    dm = DistanceMatrix()
    dm.init_cities()
    dm.init_matrix()

    main()
