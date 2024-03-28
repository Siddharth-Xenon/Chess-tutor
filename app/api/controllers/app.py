import io

import chess
import chess.engine
import chess.pgn
from fastapi import HTTPException

from app.api.utils import chess_utils


async def delete_this_route() -> dict:
    return {"msg": "This is dummy route to show basic get request"}


async def analyse_pgn(pgn_string):
    """
    Validates if the given string is a valid PGN.

    Parameters:
    - pgn_string (str): The PGN string to be validated.

    Returns:
    - A JSON response indicating whether the PGN is valid or not.
    """
    is_valid_pgn = await chess_utils.validate_pgn_format(pgn_string)
    if is_valid_pgn:
        pgn_dict = chess_utils.pgn_to_dict(pgn_string)

        moves_dict = await chess_utils.pgn_to_moves_dict(pgn_dict["Moves"][0])
        if "Moves" in pgn_dict:
            pgn_dict["Moves"] = {str(k): v for k, v in moves_dict.items()}
        save_result = await save_pgn_to_db(pgn_dict)
        analysis = await get_best_moves(pgn_string)
        critical_moments = await chess_utils.get_critical_moments(analysis, pgn_string)
        critical_moments = {str(k): v for k, v in critical_moments.items()}
        await chess_utils.save_analysis(
            analysis, pgn_dict["id"], critical_moments, pgn_dict["Moves"]
        )

        if save_result:
            pgn_dict.pop("_id", None)  # Remove ObjectId which is not serializable
            return {
                "message": "PGN saved successfully",
                "data": pgn_dict,
                "critical_moments": critical_moments,
            }

        else:
            return {
                "message": "Failed to save PGN",
                "data": pgn_dict,
                "critical_moments": critical_moments,
            }, 500

    else:
        return {"message": "Invalid PGN format", "status": "error"}, 400


async def save_pgn_to_db(pgn_dict: dict):
    """
    Saves the PGN data to the MongoDB database by calling the utility function.

    Args:
        pgn_dict (dict): A dictionary containing the PGN data.
    """
    try:
        # Ensure all keys in pgn_dict are strings to comply with MongoDB requirements
        # This includes converting the 'Moves' keys to strings if present

        # Call the utility function to save PGN data to the database
        await chess_utils.save_pgn_to_db(pgn_dict)
    except Exception as e:
        print(f"An error occurred while saving PGN data to the database: {e}")
        return False
    return True


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


async def get_best_moves(pgn_string: str):
    """
    Finds the best move at each move in the given game and returns them.

    Parameters:
    - pgn_string (str): The PGN string of the game.

    Returns:
    - A list of best moves and their evaluations for each move in the game.
    """
    pgn_io = io.StringIO(pgn_string)
    game = chess.pgn.read_game(pgn_io)

    if game is None:
        return {"error": "Invalid PGN string"}

    return await chess_utils.get_best_moves(game)


async def get_board_at_move(move_no: int, pgn_string: str):
    """
    Returns the board state at a specific move number from a given PGN string.

    Parameters:
    - move_no (int): The move number to advance to.
    - pgn_string (str): The PGN string of the game.

    Returns:
    - A JSON response with the board state at the specified move number.
    """

    try:
        pgn_io = io.StringIO(pgn_string)
        game = chess.pgn.read_game(pgn_io)

        board = game.board()
        # Iterate through the moves up to the specified move number
        for i, move in enumerate(game.mainline_moves(), start=1):
            if i == move_no:
                break
            board.push(move)
        # If the move number exceeds the total moves in the game
        if move_no > i:
            raise ValueError("Move number exceeds the total moves in the game.")
        print(board)
        return {"fen": board.fen(), "move_no": move_no}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


async def get_best_move(pgn_string: str, move_no: int):
    pgn_io = io.StringIO(pgn_string)
    game = chess.pgn.read_game(pgn_io)

    best_move, score = chess_utils.get_best_move(game, move_no)

    return {"best_move": best_move, "evaluation": score}


async def get_analysis_feed():
    documents = await chess_utils.fetch_all_documents(collection="analysis")
    for doc in documents:
        doc.pop("_id", None)
    return documents


async def get_analysis_by_id(pgn_id: str):
    document = await chess_utils.fetch_analysis(pgn_id=pgn_id)
    document.pop("_id", None)
    return document
