import random
from scipy.stats import expon

# N = 100
# M = 1000
# X = 0.008
# P_m = 0.9
# P_d = 0.05
# K = 10
# R = 10000
# T = 500
# SIZE = N * N
# INFECTION = int(M * X)

N = 5
M = 5
X = 0.008
P_m = 0.9
P_d = 0.05
K = 3
R = 10
T = 10
SIZE = N * N
INFECTION = 1
DIRECTIONS = [[-1, -1], [-1, 0], [-1, 1], [0, 1], [1, 1], [1, 0], [1, -1], [0, -1]]


class Individual:
    def __init__(self, idx, x, y, stationary, infection, immunity):
        self.idx = idx
        self.x = x
        self.y = y
        self.stationary = stationary
        self.infection = infection
        self.immunity = immunity

        self.remain_k = self.init_remain_k()
        self.direction = None

    def _get_k_period(self):
        return round(expon.ppf(random.random(), loc=K - 1))

    def init_remain_k(self):
        if self.infection:
            remain_k = self._get_k_period()
        else:
            remain_k = float('inf')
        return remain_k

    def recovery(self):
        self.infection = 0
        self.remain_k = float('inf')
        self.immunity = 1

    def infected(self):
        self.infection = 1
        self.remain_k = self._get_k_period()

    def print_info(self):
        print("idx: ", self.idx)
        print("pos: ", self.x, self.y)
        print("stationary", self.stationary)
        print("infection", self.infection)
        print("immunity", self.immunity)
        print("remain_k", self.remain_k)
        print("direction", self.direction)


def get_random_list_without_repetition(lo, hi, size):
    results = []
    while len(results) < size:
        s = random.randint(lo, hi)
        if s not in results:
            results.append(s)
    return results


def get_direction(x, y, grid):
    possible_directions = []
    for dx, dy in DIRECTIONS:
        if 0 <= x + dx < N and 0 <= y + dy < N and grid[x + dx][y + dy] is None:
            possible_directions.append((dx, dy))
    if not possible_directions:
        return None
    r = random.randint(0, len(possible_directions) - 1)
    return possible_directions[r]


def generate_population(S):
    # generate M numbers in range[0, SIZE) without repetition
    random_position = get_random_list_without_repetition(0, SIZE - 1, M)

    # generate INFECTION numbers in range[0, M) without repetition
    random_infection = get_random_list_without_repetition(0, M - 1, INFECTION)

    # generate M * S numbers in range[0, M] without repetition
    random_stationary = get_random_list_without_repetition(0, M - 1, M * S)

    population = []
    for i in range(M):
        idx = i
        pos = random_position[i]
        x = pos // N
        y = pos % N
        stationary = idx in random_stationary  # 0 is mobile, 1 is stationary
        infection = idx in random_infection  # 0 is healthy, 1 is infected
        individual = Individual(idx, x, y, stationary, infection, 0)
        population.append(individual)
    return population


def inverse_mapping(population):
    grid = [[None for _ in range(N)] for _ in range(N)]
    for individual in population:
        grid[individual.x][individual.y] = individual
    return grid


def update_healthy_state(population):
    remain_population = []
    for individual in population:
        if individual.infection:
            individual.remain_k -= 1
            if individual.remain_k == 0:
                # decide recovery or death
                if random.random() <= P_d:  # death
                    continue
                else:  # recovery
                    individual.recovery()
        remain_population.append(individual)
    return remain_population


def handle_collision(individual, neighbor):
    # case 1: both are healthy or both are infected, nothing happens
    if (not individual.infection and not neighbor.infection) or \
            (individual.infection and neighbor.infection):
        pass
    # case 2: individual is infected
    #   case 2.1: if neighbor is healthy and not immune, then he is infected
    #   case 2.2: if neighbor is healthy and immune, then nothing happens
    #   case 2.3: if neighbor is infected already, then nothing happens
    if individual.infection:
        if not neighbor.infection and not neighbor.immune:
            neighbor.infected()
        elif not neighbor.infection and neighbor.immune:
            pass
        elif neighbor.infection:
            pass
    # case 3: neighbor is infected
    #   case 3.1: if individual is healthy and not immune, then he is infected
    #   case 3.2: if individual is healthy and immune, then nothing happens
    #   case 3.3: if individual is infected already, then nothing happens
    if neighbor.infection:
        if not individual.infection and not individual.immune:
            individual.infected()
        elif not individual.infection and individual.immune:
            pass
        elif individual.infection:
            pass


def move(individual, next_x, next_y, grid):
    grid[individual.x][individual.y] = None
    individual.x = next_x
    individual.y = next_y
    grid[next_x][next_y] = individual


def update_state(population, grid):
    for individual in population:
        if individual.stationary:
            continue
        # --- decide whether need a new direction ---
        need_new_direction_flag = False
        if individual.direction:
            next_x = individual.x + individual.direction[0]
            next_y = individual.y + individual.direction[1]
            # hitting the edge
            if not (next_x >= 0 and next_x < N and next_y >= 0 and next_y < N):
                need_new_direction_flag = True
        else:
            need_new_direction_flag = True
        # get direction
        if need_new_direction_flag:
            individual.direction = get_direction(individual.x, individual.y, grid)
        # currently this individual cannot move
        if not individual.direction:
            continue

        next_x = individual.x + individual.direction[0]
        next_y = individual.y + individual.direction[1]
        # collision!!!!
        if grid[next_x][next_y] is not None:
            handle_collision(individual, grid[next_x][next_y])
            individual.direction = get_direction(individual.x, individual.y, grid)
            if individual.direction:
                move(individual, next_x, next_y, grid)
        else:
            move(individual, next_x, next_y, grid)


def terminate(population):
    if not population:
        return True
    if all([not individual.infection for individual in population]):
        return True
    return False


def simulation(S, T):
    population = generate_population(S)
    grid = inverse_mapping(population)
    for t in range(T):
        print(">t", t)
        for individual in population:
            individual.print_info()
            print("~~~")
        for i in range(N):
            tmp = []
            for j in range(N):
                if grid[i][j] is None:
                    tmp.append(0)
                else:
                    tmp.append(1)
            print(tmp)
        population = update_healthy_state(population)
        print("after update healthy")
        for individual in population:
            individual.print_info()
            print("~~~")
        if terminate(population):
            break
        update_state(population, grid)
        input()


if __name__ == '__main__':
    for run in range(R):
        #for S in [0, 0.25, 0.5, 0.75, 1.0]:
        for S in [0.5]:
            simulation(S, T)








