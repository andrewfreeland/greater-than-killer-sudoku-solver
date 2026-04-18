import numpy as np
import time

### Helper functions ###

def time_check(start_time, puzzle):
    if (int(time.time() - start_time)) > 60:
        print("Failed to find solution efficiently")
        print("Partial grid solution:")
        print(puzzle)
    return None

def get_neighbours():
    neighbours = {}
    for r in range(9):
        for c in range(9):
            cell_neigh = set()

            # Row & column
            for i in range(9):
                cell_neigh.add((r, i))
                cell_neigh.add((i, c))

            # Box
            br, bc = (r // 3) * 3, (c // 3) * 3
            for i in range(br, br+3):
                for j in range(bc, bc+3):
                    cell_neigh.add((i, j))

            cell_neigh.discard((r, c))
            neighbours[(r, c)] = cell_neigh

    return neighbours

def forward_check(domains, neighbours, cell, val):
    removed = []

    for (nr, nc) in neighbours[cell]:
        if val in domains[(nr, nc)]:
            domains[(nr, nc)].remove(val)
            removed.append((nr, nc, val))

            # No values left
            if not domains[(nr, nc)]:
                return False, removed

    return True, removed

def restore(domains, removed):
    for (r, c, val) in removed:
        domains[(r, c)].add(val)
    return domains

def choose_cell(domains):
    unassigned = [c for c in domains if len(domains[c]) > 1]
    return min(unassigned, key=lambda c: (len(domains[c]), -len(neighbours[c]))
)

def cage_feasibility(puzzle, cell, val, cage_cells, local_cage_idx, cage_targets):
    cage_sum = cage_targets[local_cage_idx]
    if cage_sum == 0:
        local_cage_feas = True
    else:
        current_cage_sum = int(sum([puzzle[new_cell[0], new_cell[1]] for new_cell in cage_cells[local_cage_idx] if tuple(new_cell) != cell]))
        if current_cage_sum + val == cage_sum:
            local_cage_feas = True
        else:
            local_cage_feas = False
    return local_cage_feas

def relation_feasibility(puzzle, cell, val, cage_to_relations, cage_cells, local_cage_idx):
    local_relation = cage_to_relations[local_cage_idx]
    if local_relation == []:
        return True
    else:
        relation_feases = []
        for relation in local_relation:
            relation_symbol = relation[-1]
            current_cage_sum = int(sum([puzzle[new_cell[0], new_cell[1]] for new_cell in cage_cells[local_cage_idx] if tuple(new_cell) != cell]))
            other_cage_idx = abs(sum(relation[:-1]) - local_cage_idx)
            other_cage_sum = int(sum([puzzle[new_cell[0], new_cell[1]] for new_cell in cage_cells[other_cage_idx] if tuple(new_cell) != cell]))
            
            if relation_symbol == "=":
                if other_cage_sum == current_cage_sum + val:
                    relation_feases.append(True)
                else:
                    relation_feases.append(False)

            elif other_cage_idx > local_cage_idx:
                if relation_symbol == "<":
                    if other_cage_sum > current_cage_sum + val:
                        relation_feases.append(True)
                    else:
                        relation_feases.append(False)
                elif relation_symbol == ">":
                    if other_cage_sum < current_cage_sum + val:
                        relation_feases.append(True)
                    else:
                        relation_feases.append(False)
            
            else:
                if relation_symbol == "<":
                    if other_cage_sum < current_cage_sum + val:
                        relation_feases.append(True)
                    else:
                        relation_feases.append(False)
                elif relation_symbol == ">":
                    if other_cage_sum > current_cage_sum + val:
                        relation_feases.append(True)
                    else:
                        relation_feases.append(False)

    return np.all(relation_feases)

def assign(puzzle, cell, val, domains):
    puzzle[cell[0], cell[1]] = val
    domains[cell].remove(val)
    return (puzzle, domains)

def setup():
    input_puzzle = np.zeros((9,9), dtype=int)

    # Precomputed variables:
    # domains = cell: possible values
    # neighbours = cell: neighbouring cells
    # cell_to_cage = cell: cage index
    # cage_cells = list of cells in each cage
    # cage_targets = list of sums for each cage
    # cage_sizes = size of each cage
    # cage_to_relations = cage index: (cage index 1, cage index 2, relation symbol); can be empty for no relation

    domains = {(r, c): set(range(1, 10)) for r in range(9) for c in range(9)}
    neighbours = get_neighbours()

    cell_to_cage = {}
    for i, cage in enumerate(cage_input):
        for (r, c) in cage[:-1]:
            cell_to_cage[(r, c)] = i

    cage_cells = [cage[:-1] for cage in cage_input]
    cage_targets = [cage[-1] for cage in cage_input]
    cage_sizes = [len(cage[:-1]) for cage in cage_input]

    cage_to_relations = {i: [] for i in range(len(cage_input))}

    for rel in relations_input:
        c1, c2, op = rel
        cage_to_relations[c1].append((c1, c2, op))
        cage_to_relations[c2].append((c1, c2, op))

    return (input_puzzle, domains, neighbours, cell_to_cage, cage_cells, 
            cage_targets, cage_sizes, cage_to_relations)

### Main ###

def solve(puzzle, domains):
    if not np.any(puzzle == 0):
        return True
    
    cell = choose_cell(domains)
    current_cell_domain = domains[cell]

    for val in current_cell_domain:

        # Neighbour check
        neighbour_bool = not np.any(val == [puzzle[neighbour] for neighbour in neighbours[cell]])

        local_cage_idx = cell_to_cage[cell]

        # Cage feasibility check
        local_cage_feas = cage_feasibility(puzzle, cell, val, cage_cells, local_cage_idx, cage_targets)

        # Relation feasibility check
        local_relation_feas = relation_feasibility(puzzle, cell, val, cage_to_relations, cage_cells, local_cage_idx)

        # Final validation
        if neighbour_bool and local_cage_feas and local_relation_feas:
            puzzle, domains = assign(puzzle, cell, val, domains)

            (forward_bool, removed) = forward_check(domains, neighbours, cell, val)
            if forward_bool:
                if solve(puzzle, domains):
                    return True
            
            domains = restore(domains, removed)

    return False

if __name__ == "__main__":

    # Cages consist of grid indices defining cage, and sum as last element
    # Cages exist in list of cages
    cage_input = [[[0, 0], [1, 0], [1, 1], 0], 
                  [[0, 1], [0, 2], 11],
                  [[0, 3], [0, 4], 0],
                  [[0, 5], [0, 6], [0, 7], 0],
                  [[0, 8], [1, 8], [2, 8], 13],
                  [[1, 2], [1, 3], [1, 4], 17],
                  [[1, 5], [1, 6], 8],
                  [[1, 7], [2, 7], [3, 7], 17],
                  [[2, 0], [2, 1], 0],
                  [[2, 2], [2, 3], 13],
                  [[2, 4], [2, 5], 8],
                  [[2, 6], [3, 6], 7],
                  [[3, 0], [3, 1], [3, 2], 0],
                  [[3, 3], [3, 4], [3, 5], 0],
                  [[3, 8], [4, 8], [5, 8], 19],
                  [[4, 0], [4, 1], 11],
                  [[4, 2], [4, 3], 0],
                  [[4, 4], [4, 5], [4, 6], [4, 7], 0],
                  [[5, 0], [5, 1], [5, 2], 0],
                  [[5, 3], [5, 4], [5, 5], 18],
                  [[5, 6], [6, 6], 0],
                  [[5, 7], [6, 7], [7, 7], 0],
                  [[6, 0], [6, 1], 14],
                  [[6, 2], [6, 3], 6],
                  [[6, 4], [6, 5], 0],
                  [[6, 8], [7, 8], [8, 8], 0],
                  [[7, 0], [7, 1], [8, 0], 10],
                  [[7, 2], [7, 3], [7, 4], 16],
                  [[7, 5], [7, 6], 0],
                  [[8, 1], [8, 2], 14],
                  [[8, 3], [8, 4], 6],
                  [[8, 5], [8, 6], [8, 7], 16]]

    # Key: [1st cage index, 2nd cage index, relation]
    # Relations: <, >, =
    relations_input = [[2, 3, ">"],
                       [3, 4, ">"],
                       [8, 12, ">"],
                       [9, 13, "<"],
                       [12, 13, ">"],
                       [12, 16, "<"],
                       [16, 19, "<"],
                       [17, 20, "="],
                       [21, 25, "<"], 
                       [21, 28, "<"],
                       [24, 27, "<"]]

    (input_puzzle, domains, neighbours, cell_to_cage, cage_cells, 
            cage_targets, cage_sizes, cage_to_relations) = setup()

    print(solve(input_puzzle, domains))