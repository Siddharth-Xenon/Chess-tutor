from fastapi import APIRouter, Depends, HTTPException
from fastapi_jwt_auth import AuthJWT
import chess.pgn
import io

from app.api.controllers import app

router = APIRouter()


@router.get("/delete_this_route")
async def delete_this_route(
    Authorize: AuthJWT = Depends(),
):
    res: dict = await app.delete_this_route()
    return res


@router.post("/pgn")
async def validate_pgn(pgn_string: str):
    """
    Validates if the given string is a valid PGN.
    
    Parameters:
    - pgn_string (str): The PGN string to be validated.

    Returns:
    - A JSON response indicating whether the PGN is valid or not.
    """
    is_valid_pgn = await app.validate_pgn_format(pgn_string)
    if is_valid_pgn:
        pgn_dict = app.pgn_to_dict(pgn_string)

        moves_dict = app.moves_to_dict(pgn_dict["Moves"][0])
        print(moves_dict)
        pgn_dict["Moves"] = moves_dict
        save_result = await app.save_pgn_to_db(pgn_dict)
        if save_result:
            pgn_dict.pop("_id", None)  # Remove ObjectId which is not serializable
            # Attempt to parse the PGN string
            pgn_io = io.StringIO(pgn_string)
            game = chess.pgn.read_game(pgn_io)
            print(game)
            return {"message": "PGN saved successfully", "data": pgn_dict}
        else:
            return {"message": "Failed to save PGN", "status": "error"}, 500

    else:
        return {"message": "Invalid PGN format", "status": "error"}, 400
        
            
@router.get("/board/{move_no}")
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
    
@router.get("/get_best_move")
async def getBestMove(pgn_string: str, move_no: int):

    pgn_io = io.StringIO(pgn_string)
    game = chess.pgn.read_game(pgn_io)

    best_move, score = app.get_best_move( game, move_no)

    return {"best_move": best_move, "evaluation": score}

@router.get("/get_best_moves")
async def getBestMoves(pgn_string: str):
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

    best_moves = app.get_best_moves(game)
    return {"best_moves": best_moves}