import re
import chess
import chess.engine
import io
import chess.pgn
from app.api.utils import chess_utils
from typing import List, Tuple


async def delete_this_route() -> dict:
    return {"msg": "This is dummy route to show basic get request"}


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
    pgn_dict["id"] = chess_utils.generate_hex_uuid()
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


async def save_pgn_to_db(pgn_dict: dict):
    """
    Saves the PGN data to the MongoDB database by calling the utility function.

    Args:
        pgn_dict (dict): A dictionary containing the PGN data.
    """
    try:
        # Call the utility function to save PGN data to the database

        await chess_utils.save_pgn_to_db(pgn_dict)
    except Exception as e:
        print(f"An error occurred while saving PGN data to the database: {e}")
        return False
    return True


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

def go_to_move_number(game, move_number):
    """
    Advances the game to a specific move number and returns the board at that position.

    Parameters:
    - game (chess.pgn.Game): The game object.
    - move_number (int): The move number to advance to.

    Returns:
    - chess.Board: The board position at the specified move number.
    """
    # Initialize a board from the game's starting position
    board = game.board()
    # Iterate over the mainline moves up to the specified move number
    for move in game.mainline_moves():
        if board.fullmove_number > move_number:
            break
        board.push(move)
    return board

def get_best_move( game, move_number):
    """
    Uses Stockfish to predict the best move at a specified move number in a given game.

    Parameters:
    - game (str): The game.
    - move_number (int): The move number for which to predict the best move.

    Returns:
    - A tuple of (best move in UCI format, evaluation score).
    """

    stockfish_path = "./stockfish/stockfish-windows-x86-64-avx2.exe"
    
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
        score = evaluation.white().score(mate_score=100000) if board.turn == chess.WHITE else evaluation.black().score(mate_score=-100000)
    else:
        score = None

    return result.move.uci(), score

def get_best_moves(game) -> List[Tuple[str, int]]:
    """
    Analyzes the entire game, predicting the best move at each position.

    Parameters:
    - game (chess.pgn.Game): The game to analyze.

    Returns:
    - A list of tuples with best moves in UCI format and their evaluation scores.
    """
    stockfish_path = "./stockfish/stockfish-windows-x86-64-avx2.exe"
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