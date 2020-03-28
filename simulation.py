import random
import time
from scipy.stats import expon

N = 100
M = 1000
X = 0.008
P_m = 0.9
P_d = 0.05
K = 10
R = 10000
T = 500
SIZE = N * N
INFECTION_NUMBER = int(M * X)
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
        self.quarantined = False

    def _get_k_period(self):
        return round(expon.ppf(random.random(), loc=K-1))

    def init_remain_k(self):
        if self.infection:
            remain_k = self._get_k_period()
        else:
            remain_k = float('inf')
        return remain_k

    def recovery(self):
        self.infection = False
        self.remain_k = float('inf')
        self.immunity = True

    def infected(self):
        self.infection = True
        self.remain_k = self._get_k_period()


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
    random_infection = get_random_list_without_repetition(0, M - 1, INFECTION_NUMBER)

    # generate M * S numbers in range[0, M] without repetition
    random_stationary = get_random_list_without_repetition(0, M - 1, M * S)

    population = []
    for i in range(M):
        idx = i
        pos = random_position[i]
        x = pos // N
        y = pos % N
        stationary = idx in random_stationary
        infection = idx in random_infection
        individual = Individual(idx, x, y, stationary, infection, False)
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
    # case 1:
    # - both are healthy
    # - both are infected
    # - individual is infected but quarantined
    # - neighbor is infected but quarantined
    # Then nothing happens
    if (not individual.infection and not neighbor.infection) or \
            (individual.infection and neighbor.infection) or \
            (individual.infection and individual.quarantined) or \
            (neighbor.infection and neighbor.quarantined):
        return
    # case 2: individual is infected (no quarantined)
    #   case 2.1: if neighbor is healthy and not immunity, then he is infected
    #   case 2.2: if neighbor is healthy and immunity, then nothing happens
    #   case 2.3: if neighbor is infected already, then nothing happens
    if individual.infection:
        if not neighbor.infection and not neighbor.immunity:
            neighbor.infected()
        elif not neighbor.infection and neighbor.immunity:
            pass
        elif neighbor.infection:
            pass
        return
    # case 3: neighbor is infected (no quarantined)
    #   case 3.1: if individual is healthy and not immunity, then he is infected
    #   case 3.2: if individual is healthy and immunity, then nothing happens
    #   case 3.3: if individual is infected already, then nothing happens
    if neighbor.infection:
        if not individual.infection and not individual.immunity:
            individual.infected()
        elif not individual.infection and individual.immunity:
            pass
        elif individual.infection:
            pass
        return


def move(individual, next_x, next_y, grid):
    grid[individual.x][individual.y] = None
    individual.x = next_x
    individual.y = next_y
    grid[next_x][next_y] = individual


def update_state(population, grid):
    for individual in population:
        # stationary or decide not to move
        if individual.stationary or random.random() >= P_m:
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
                next_x = individual.x + individual.direction[0]
                next_y = individual.y + individual.direction[1]
                move(individual, next_x, next_y, grid)
        else:
            move(individual, next_x, next_y, grid)


def test_and_quarantine(population, test_rate):
    # select test individuals randomly.
    # If individuals <= test number, then all test
    test_number = M * test_rate
    if len(population) <= test_number:
        test_idx = [i for i in range(len(population))]
    else:
        test_idx = get_random_list_without_repetition(0, len(population) - 1, test_number)

    # test and quarantine if infected
    for idx in test_idx:
        if population[idx].infection:
            population[idx].quarantined = True


def terminate(population):
    if not population:
        return True
    if all([not individual.infection for individual in population]):
        return True
    return False


def simulation(S, T):
    population = generate_population(S)
    grid = inverse_mapping(population)
    break_t = T
    for t in range(T):
        population = update_healthy_state(population)
        if terminate(population):
            break_t = t
            break
        update_state(population, grid)
    return break_t


def simulation_with_quarantine(S, T, test_rate):
    population = generate_population(S)
    grid = inverse_mapping(population)
    break_t = T
    max_infection = 0
    for t in range(T):
        max_infection = max(max_infection, sum([i.infection for i in population]))
        population = update_healthy_state(population)
        if terminate(population):
            break_t = t
            break
        test_and_quarantine(population, test_rate)
        update_state(population, grid)
    return break_t, max_infection

if __name__ == '__main__':
    for run in range(R):
        print("#run", run)
        st = time.time()
        for S in [0, 0.25, 0.5, 0.75, 1.0]:
            # break_t = simulation(S, T)
            break_t, max_infection = simulation_with_quarantine(S, T, test_rate=0.1)
            print("S=%.2f, break T=%d, max_infaction=%d" % (S, break_t, max_infection))
        print("cost time for #run %d: %.2f" % (run, time.time() - st))








