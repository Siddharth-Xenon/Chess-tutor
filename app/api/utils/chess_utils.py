import re
import uuid
from typing import List, Tuple

import chess
import chess.engine
import chess.pgn
from fastapi import HTTPException

from app.db.mongo_client import ZuMongoClient

from app.core.config import (
    Stockfish
)


async def validate_pgn_format(pgn_string: str) -> bool:
    """
    Validates if the given text is in correct PGN format.

    Args:
        pgn_string (str): The PGN string to validate.

    Returns:
        bool: True if the PGN format is correct, False otherwise.
    """

    # Define a regular expression pattern for PGN format validation
    # print(pgn_string)
    pgn_pattern = r"""
        (\[Event\s+".*"\]\s*)?
        (\[Site\s+".*"\]\s*)?
        (\[Date\s+"\d{4}\.\d{2}\.\d{2}"\]\s*)?
        (\[Round\s+".*"\]\s*)?
        (\[White\s+".*"\]\s*)?
        (\[Black\s+".*"\]\s*)?
        (\[Result\s+".*"\]\s*)?
        (\[CurrentPosition\s+".*"\]\s*)?
        (\[Timezone\s+".*"\]\s*)?
        (\[ECO\s+".*"\]\s*)?
        (\[ECOUrl\s+".*"\]\s*)?
        (\[UTCDate\s+"\d{4}\.\d{2}\.\d{2}"\]\s*)?
        (\[UTCTime\s+"\d{2}:\d{2}:\d{2}"\]\s*)?
        (\[WhiteElo\s+"\d*"\]\s*)?
        (\[BlackElo\s+"\d*"\]\s*)?
        (\[TimeControl\s+".*"\]\s*)?
        (\[Termination\s+".*"\]\s*)?
        (\[StartTime\s+".*"\]\s*)?
        (\[EndDate\s+"\d{4}\.\d{2}\.\d{2}"\]\s*)?
        (\[EndTime\s+".*"\]\s*)?
        (\[Link\s+".*"\]\s*)?
        (\[WhiteUrl\s+".*"\]\s*)?
        (\[WhiteCountry\s+".*"\]\s*)?
        (\[WhiteTitle\s+".*"\]\s*)?
        (\[BlackUrl\s+".*"\]\s*)?
        (\[BlackCountry\s+".*"\]\s*)?
        (\[BlackTitle\s+".*"\]\s*)?
        (\d+\.\s+([a-zA-Z0-9+]+(\s+[a-zA-Z0-9+]+)?\s*)+)
    """

    # Use VERBOSE flag to allow multi-line regex for better readability
    match = re.match(pgn_pattern, pgn_string, re.VERBOSE)

    return bool(match)


def pgn_to_dict(pgn_string: str) -> dict:
    """
    Converts a PGN string to a dictionary with key-value pairs.

    Args:
        pgn_string (str): The PGN string to convert.

    Returns:
        dict: A dictionary representation of the PGN string.
    """
    pgn_dict = {}
    pgn_dict["id"] = generate_hex_uuid()
    # Initialize a list to accumulate move data
    moves_list = []
    # Iterate over the string character by character
    i = 0
    while i < len(pgn_string):
        # Check if the current part of the string contains PGN metadata
        if pgn_string[i] == "[":
            end_bracket_index = pgn_string.find("]", i)
            line = pgn_string[i : end_bracket_index + 1]
            # Extract the key and value
            key = line.split(" ")[0][1:]
            value = line.split('"')[1]
            pgn_dict[key] = value
            i = end_bracket_index + 1
        # Accumulate move data if not part of metadata
        else:
            move_start = i
            while i < len(pgn_string) and pgn_string[i] != "[":
                i += 1
            move_data = pgn_string[move_start:i].strip()
            if move_data:
                moves_list.append(move_data)
            # Skip to the next character without incrementing i as it's already at the start of the next segment or end of string
    # Add accumulated moves data to the dictionary under a special key, if any
    if moves_list:
        pgn_dict["Moves"] = moves_list
    return pgn_dict


def generate_hex_uuid():
    """
    Generates a unique hex UUID.

    Returns:
        str: A string representation of a hex UUID.
    """
    return uuid.uuid4().hex


def moves_to_dict(moves_str: str) -> dict:
    """
    Converts a string of moves separated by move identifiers into a dictionary with move numbers as keys.

    Args:
        moves_str (str): A string of moves separated by identifiers like "1.", "2.", ...

    Returns:
        dict: A dictionary with move numbers as keys and a list of individual moves as values.
    """
    moves_dict = {}
    # Split the string into individual moves based on the move number identifiers
    moves_list = [
        move.strip() for move in re.split(r"\d+\.", moves_str) if move.strip()
    ]
    for index, move in enumerate(moves_list, start=1):
        # The move number is the index in this case
        move_number = f"{index}."
        # Split the move into individual parts, might include captures, checks, etc.
        individual_moves = move.split(" ")
        # Filter out empty strings that may result from extra spaces
        individual_moves = [move for move in individual_moves if move]
        moves_dict[move_number] = individual_moves
    return moves_dict


async def save_pgn_to_db(pgn_dict):
    """
    Saves the PGN data to the MongoDB database.

    Args:
        pgn_dict (dict): A dictionary containing the PGN data.
    """
    # Assuming there's a collection specifically for storing PGN data
    # and 'pgn_dict' contains all necessary data including a unique 'id'
    try:
        # Insert the PGN data into the 'pgn_data' collection
        await ZuMongoClient.insert_one(
            col="pgn_data", insert_data=pgn_dict, handle_exception=False
        )
        print("PGN data saved successfully.")
    except Exception as e:
        print(f"Failed to save PGN data to DB. Error: {e}")


async def save_analysis(
    analysis: str,
    pgn_id: str,
    critical_moments: dict,
    moves: dict,
    openai_analysis: dict,
):
    analysis_dict = {
        "id": generate_hex_uuid(),
        "pgn_id": pgn_id,
        "moves": moves,
        "critical_moments": critical_moments,
        "analysis": analysis,
        "openai_analysis": openai_analysis,
    }

    try:
        await ZuMongoClient.insert_one(
            col="analysis", insert_data=analysis_dict, handle_exception=False
        )
        print("Analysis saved successfully.")
    except Exception as e:
        print(f"Failed to save analysis to DB. Error: {e}")


async def get_best_move(game, move_number):
    """
    Uses Stockfish to predict the best move at a specified move number in a given game.

    Parameters:
    - game (str): The game.
    - move_number (int): The move number for which to predict the best move.

    Returns:
    - A tuple of (best move in UCI format, evaluation score).
    """

    stockfish_path = Stockfish.STOCKFISH_PATH

    # Go to the specified move number in the game
    board = game.board()
    for i, move in enumerate(game.mainline_moves(), start=1):
        board.push(move)
        if i == move_number:
            break

    # Initialize the Stockfish engine
    with chess.engine.SimpleEngine.popen_uci(stockfish_path) as engine:
        # Ask Stockfish for the best move at the current position
        result = engine.play(board, chess.engine.Limit(time=0.1))

        # Optional: Get evaluation of the position
        info = engine.analyse(board, chess.engine.Limit(depth=20))
        evaluation = info.get("score", None)

    # Convert the evaluation to a more readable format
    if evaluation is not None:
        # Adjust the score for the side to move
        score = (
            evaluation.white().score(mate_score=100000)
            if board.turn == chess.WHITE
            else evaluation.black().score(mate_score=-100000)
        )
    else:
        score = None

    return result.move.uci(), score


async def get_best_moves(game) -> List[Tuple[str, int]]:
    """
    Analyzes the entire game, predicting the best move at each position.

    Parameters:
    - game (chess.pgn.Game): The game to analyze.

    Returns:
    - A list of tuples with best moves in UCI format and their evaluation scores.
    """
    stockfish_path = Stockfish.STOCKFISH_PATH
    best_moves = []

    board = game.board()
    with chess.engine.SimpleEngine.popen_uci(stockfish_path) as engine:
        for move in game.mainline_moves():
            board.push(move)
            result = engine.play(board, chess.engine.Limit(time=0.1))
            info = engine.analyse(board, chess.engine.Limit(depth=20))
            evaluation = info.get("score", None)

            if evaluation is not None:
                if evaluation.is_mate():
                    score = f"Mate in {abs(evaluation.mate())} by {'White' if evaluation.mate() > 0 else 'Black'}"
                else:
                    score = evaluation.white().score(mate_score=10000)
            else:
                score = "N/A"

            best_moves.append((result.move.uci(), score))

    return best_moves


async def pgn_to_moves_dict(pgn_string: str) -> dict:
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


# Find and print the critical moments
async def get_critical_moments(analysis: str, pgn: str) -> dict:
    critical_moments = find_critical_moments(analysis)
    moves_dict = await pgn_to_moves_dict(pgn)
    critical_moments_dict = {
        i + 1: moves_dict.get(i + 1, "N/A") for i in critical_moments
    }
    print(critical_moments_dict)
    return critical_moments_dict


async def fetch_all_documents(collection: str):
    try:
        cursor = ZuMongoClient.find(
            col=collection,
            filter_data={},
            project={"id": 1, "pgn_id": 1, "moves": 1, "critical_moments": 1},
        )
        documents = await cursor.to_list(length=None)
        return documents
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch documents from {collection}: {str(e)}",
        )


async def fetch_analysis(pgn_id: str):
    return await ZuMongoClient.find_one(col="analysis", filter_data={"pgn_id": pgn_id})
