import re

analysis = [
    ["d7d5", 32],
    ["g1f3", 17],
    ["b8c6", 25],
    ["f1b5", 22],
    ["f8c5", 27],
    ["f3g5", 631],
    ["g8f6", 636],
    ["d2d4", 659],
    ["d8e6", 667],
    ["c3d5", 673],
    ["c8g4", 188],
]

pgn_str = """
1. e4 e5 2. Nf3 Nc6 3. Bc4 Qg5 4. Nxg5 Nd8 5. Nc3 d5 6. Qg4 1-0
"""


def find_critical_moments(analysis):
    critical_moments = []
    # Iterate through analysis list, except the last item to avoid index out of range
    for i in range(len(analysis) - 1):
        # Calculate the absolute difference in evaluation between consecutive moves
        eval_diff = abs(analysis[i + 1][1] - analysis[i][1])
        # Check if the difference is at least 100 points
        if eval_diff >= 200:
            # Calculate move number; add 1 because indexing starts at 0, then divide by 2 and round up
            critical_moments.append(i + 1)
    return critical_moments


def pgn_to_moves_dict(pgn_string: str) -> dict:
    """
    Converts a string of moves separated by move identifiers into a dictionary with move numbers as keys and moves as values.

    Args:
        pgn_string (str): A string of moves separated by identifiers like "1.", "2.", ...

    Returns:
        dict: A dictionary with move numbers as keys and moves as values.
        {1: 'e4', 2: 'b6', 3: 'c4', 4: 'Bb7', 5: 'Nc3', 6: 'e6'}
    """
    moves_dict = {}
    # Split the string into individual moves based on the move number identifiers
    moves_list = [
        move.strip() for move in re.split(r"\d+\.", pgn_string) if move.strip()
    ]
    move_counter = 1
    for move in moves_list:
        # Split the move into individual parts, might include captures, checks, etc.
        individual_moves = move.split(" ")
        # Filter out empty strings that may result from extra spaces
        individual_moves = [move for move in individual_moves if move]
        for individual_move in individual_moves:
            moves_dict[move_counter] = individual_move
            move_counter += 1
    return moves_dict


# Analysis data


# Find and print the critical moments
def get_critical_moments(analysis: str) -> dict:
    critical_moments = find_critical_moments(analysis)
    moves_dict = pgn_to_moves_dict(pgn_str)
    critical_moments_dict = {i + 1: moves_dict[i + 1] for i in critical_moments}
    print(critical_moments_dict)
    return critical_moments_dict
