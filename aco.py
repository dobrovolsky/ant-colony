import random

import structlog

log = structlog.get_logger()


class Graph(object):
    def __init__(self, cost_matrix: list):
        self.matrix = cost_matrix
        self.rank = len(self.matrix)
        self.pheromone = [[1 / self.rank ** 2 for j in range(self.rank)] for i in range(self.rank)]


class ACO(object):
    def __init__(
            self,
            ant_count: int,
            run_without_improvement: int,
            alpha: float,
            beta: float,
            rho: float,
            q: float,
            pheromone_strategy: str,
    ):
        """
        :param ant_count:
        :param run_without_improvement:
        :param alpha: relative importance of pheromone (distance)
        :param beta: relative importance of heuristic information (pheromone)
        :param rho: pheromone evaporation coefficient
        :param q: pheromone intensity on passed path
        :param pheromone_strategy: pheromone update ant_cycle, ant_quality, ant_density
        """

        self.Q = q
        self.rho = rho
        self.beta = beta
        self.alpha = alpha
        self.ant_count = ant_count
        self.run_without_improvement = run_without_improvement
        self.strategy_pheromone_updating = pheromone_strategy

    def update_pheromone(self, graph: Graph, ants: list):
        for i, row in enumerate(graph.pheromone):
            for j, col in enumerate(row):
                graph.pheromone[i][j] *= self.rho
                for ant in ants:
                    graph.pheromone[i][j] += ant.pheromone_delta[i][j]

    def solve(self, graph: Graph):
        best_cost = float('inf')
        best_solution = []
        count = 0

        while count < self.run_without_improvement:
            ants = [Ant(self, graph) for i in range(self.ant_count)]
            for ant in ants:
                for i in range(graph.rank - 1):
                    ant.select_next()

                if ant.total_cost < best_cost:
                    best_cost = ant.total_cost
                    best_solution = ant.visited
                    count = 0
                    log.info(f'find better solution', cost=best_cost, best_solution=best_solution)
                ant.update_pheromone_on_path()
            self.update_pheromone(graph, ants)
            count += 1

        return best_solution, best_cost


class Ant(object):
    def __init__(self, aco: ACO, graph: Graph):
        self.colony = aco
        self.graph = graph
        self.total_cost = 0.0
        self.visited = []
        self.pheromone_delta = []  # the local increase of pheromone
        self.allowed = [i for i in range(graph.rank)]
        self.tau = [[0 if i == j else 1 / graph.matrix[i][j] for j in range(graph.rank)] for i in
                    range(graph.rank)]

        start_node = random.randint(0, graph.rank - 1)
        self.visited.append(start_node)
        self.current = start_node
        self.allowed.remove(start_node)

    def get_probability(self, _sum, i):
        return self.graph.pheromone[self.current][i] ** self.colony.alpha * \
               self.tau[self.current][i] ** self.colony.beta / _sum

    def select_next(self):
        all_city_sum = 0
        for i in self.allowed:
            all_city_sum += self.graph.pheromone[self.current][i] ** self.colony.alpha * \
                            self.tau[self.current][i] ** self.colony.beta

        probabilities = [self.get_probability(_sum=all_city_sum, i=i)
                         if i in self.allowed else 0 for i in range(self.graph.rank)]

        selected = 0
        rand = random.random()
        for i, probability in enumerate(probabilities):
            rand -= probability
            if rand <= 0:
                selected = i
                break
        self.allowed.remove(selected)
        self.visited.append(selected)
        self.total_cost += self.graph.matrix[self.current][selected]
        self.current = selected

    def update_pheromone_on_path(self):
        self.pheromone_delta = [[0 for j in range(self.graph.rank)] for i in range(self.graph.rank)]
        for previous_index, current in enumerate(self.visited[1:]):
            previous = self.visited[previous_index]
            if self.colony.strategy_pheromone_updating == 'ant_quality':
                self.pheromone_delta[previous][current] = self.colony.Q
            elif self.colony.strategy_pheromone_updating == 'ant_density':
                self.pheromone_delta[previous][current] = self.colony.Q / self.graph.matrix[previous][current]
            elif self.colony.strategy_pheromone_updating == 'ant_cycle':
                self.pheromone_delta[previous][current] = self.colony.Q / self.total_cost
