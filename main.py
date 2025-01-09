import copy
import math
import random

import numpy as np
from deap import base, creator, tools, algorithms
from faker import Faker
from colorama import Fore, Style

from structures import Group, Types, Field

size = 2
faker = Faker()
group_names = [faker.street_name() for _ in range(math.floor(((size * 4) - 8) // 3) + 1)]
field_names = [faker.user_name() for _ in range(len(group_names) * 3)]


def generate_board():
    if size < 2:
        raise ValueError("The board size must be at least 2.")
    groups = copy.deepcopy(group_names)
    fields = copy.deepcopy(field_names)
    new_fields = []
    max_fields = (size * 4) + 4

    rails = Group(Types.RAILROAD, "KD")
    corners = Group(Types.CORNER, "Narozniki")
    corner_seq = ["Start", "Więzenie", "Parking", "Idź do więzienia"]
    special_seq = ["Szansa1", "Szansa2", "Podatek 50", "Podatek 75"]
    specials = Group(Types.SPECIAL, "Szansy")

    for i in range(4):
        new_fields.append(Field(rails, f"Kolej_{i}"))
        new_fields.append(Field(corners, corner_seq[i]))
        new_fields.append(Field(specials, special_seq[i]))

    no_fields = len(new_fields)
    group = None
    members = 0
    while no_fields < max_fields:
        if group is None:
            group = Group(Types.CITY, groups.pop())
            members = 0

        new_fields.append(Field(group, fields.pop()))
        members += 1
        no_fields += 1

        if members == 3:
            group = None

    random.shuffle(new_fields)
    Group.reset_id()
    return new_fields


def display_board(board: list[Field]):
    if len(board) % 4 != 0:
        raise ValueError("The board must have a number of fields divisible by 4 for a rectangular layout.")

    field_width = 25
    field_height = 5

    group_colors = {
        "RAILROAD": Fore.GREEN,
        "CITY": Fore.BLUE,
        "CORNER": Fore.YELLOW,
        "SPECIAL": Fore.RED,
    }

    # Determine the size of each side
    side_length = len(board) // 4
    side_length = size + 2

    # Helper function to create a rectangle for one field
    def format_field(field):
        color = group_colors.get(field.group.type.name, Fore.WHITE)  # Default color is white
        lines = []
        lines.append(color + "+" + "-" * (field_width - 2) + "+" + Style.RESET_ALL)  # Top border

        if field.group.type == Types.CITY:
            lines.append(color + "|" + f" ID: {field.group.id}".center(field_width - 2) + "|" + Style.RESET_ALL)
        else:
            lines.append(color + "|" + "---".center(field_width - 2) + "|" + Style.RESET_ALL)  # Empty line

        lines.append(
            color + "|" + f"{field.id}".center(field_width - 2) + "|" + Style.RESET_ALL)  # ID in the center
        lines.append(
            color + "|" + f"Gr({field.group.name})".center(field_width - 2) + "|" + Style.RESET_ALL)  # Group name
        lines.append(color + "+" + "-" * (field_width - 2) + "+" + Style.RESET_ALL)  # Bottom border
        return lines

    # Split the board into sections
    top_row = board[:size+2]
    right_column = board[size+2:len(board) // 2]
    bottom_row = board[len(board) // 2:len(board) // 2 + size + 2][::-1]
    left_column = board[len(board) // 2 + size + 2:len(board)][::-1]

    # Generate text for each row
    top_row_lines = ["".join([format_field(field)[line] for field in top_row]) for line in range(field_height)]
    bottom_row_lines = ["".join([format_field(field)[line] for field in bottom_row]) for line in
                        range(field_height)]

    # Render the middle rows
    middle_rows = []
    for i in range(side_length - 2):
        left_field_lines = format_field(left_column[i])
        right_field_lines = format_field(right_column[i])
        for j in range(field_height):
            middle_rows.append(left_field_lines[j] + " " * (field_width * (side_length - 2)) + right_field_lines[j])

    # Combine everything into the full board
    print("\n".join(top_row_lines))
    print("\n".join(middle_rows))
    print("\n".join(bottom_row_lines))


# Evaluation function
def calculate_balance_score(board):
    # Count the occurrences of each property type
    property_counts = {
        "Street": board.count("Street"),
        "Chance": board.count("Chance"),
        "Railroad": board.count("Railroad"),
        "Utility": board.count("Utility")
    }

    # Total number of properties (40 spaces on the board)
    total_properties = len(board)

    # Calculate the target count for each property type (balanced distribution)
    target_count = total_properties / len(property_counts)

    # Calculate the balance score based on the deviation from target count
    balance_score = 0
    for property_type, count in property_counts.items():
        # Penalize large deviations from the target count
        balance_score -= abs(count - target_count)

    return balance_score


def calculate_aesthetic_score(board):
    distance_penalty = 0

    last_pos_rail = -1
    last_pos_special = -1
    for idx, space in enumerate(board):
        if space.group.type == Types.RAILROAD:
            if last_pos_rail != -1:
                distance_penalty -= abs(idx - last_pos_rail)
            last_pos_rail = idx
        if space.group.type == Types.SPECIAL:
            if last_pos_special != -1:
                distance_penalty -= abs(idx - last_pos_special)
            last_pos_special = idx

    all_groups = set([space.group for space in board])

    groups = {}
    for idx, member in enumerate(board):
        if member.group.type != Types.CITY:
            continue

        if member.group.name not in groups:
            groups[member.group.name] = [idx]
        else:
            groups[member.group.name].append(idx)

    clustering_penalty = 0
    for group in groups:
        for i in range(len(groups[group]) - 1):
            clustering_penalty += abs(groups[group][i] - groups[group][i + 1])

    corners_penalty = 0
    corners = [0, size + 1, 2 * size + 2, 3 * size + 3]
    total_fields = len(board)
    for group in all_groups:
        if group.type == Types.CORNER:
            positions = [idx for idx, space in enumerate(board)
                         if space.group.name == group.name]
            for pos in positions:
                min_corner_dist = min(
                    min(abs(pos - corner), total_fields - abs(pos - corner))
                    for corner in corners
                )
                corners_penalty += min_corner_dist

    aesthetic_score = distance_penalty + clustering_penalty + corners_penalty

    return aesthetic_score


def evaluate(board):
    # Define the two objectives: Balance and Aesthetics
    balance_score = calculate_balance_score(board)
    aesthetic_score = calculate_aesthetic_score(board)

    # Return both scores as a tuple (minimizing both)
    return balance_score, aesthetic_score


if __name__ == "__main__":
    boards = []
    values = []
    for _ in range(1000000):
        # print(calculate_balance_score(val))
        board = generate_board()

        boards.append(board)
        values.append(calculate_aesthetic_score(board))
    values = np.array(values)
    print(f"Min: {np.min(values)}, Max: {np.max(values)}, Std: {np.std(values)}, Mean: {np.mean(values)}")
    display_board(boards[np.argmin(values)])

    # creator.create("FitnessMulti", base.Fitness, weights=(1.0, -1.0))  # First objective (maximize), second (minimize)
    # creator.create("Individual", list, fitness=creator.FitnessMulti)
    #
    # toolbox = base.Toolbox()
    # toolbox.register("individual", tools.initIterate, creator.Individual, generate_board)
    # toolbox.register("population", tools.initRepeat, list, toolbox.individual)
    # toolbox.register("mate", tools.cxTwoPoint)
    # toolbox.register("mutate", tools.mutShuffleIndexes, indpb=0.2)
    # toolbox.register("select", tools.selNSGA2)
    # toolbox.register("evaluate", evaluate)
    #
    # # Create the population
    # population = toolbox.population(n=100)
    #
    # # Run the genetic algorithm
    # algorithms.eaMuPlusLambda(population, toolbox, mu=100, lambda_=200, cxpb=0.7, mutpb=0.2, ngen=50)
    #
    # # Extract and print Pareto front
    # pareto_front = tools.sortNondominated(population, len(population), first_front_only=True)[0]
    # print("Pareto Front (Balance vs Aesthetic):")
    # for ind in pareto_front:
    #     print(ind.fitness.values)
