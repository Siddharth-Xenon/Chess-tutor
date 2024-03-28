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
    return await app.validate_pgn(pgn_string=pgn_string)
        
            
@router.get("/board/{move_no}")
async def get_board_at_move(move_no: int, pgn_string: str):
   return await app.get_board_at_move(move_no=move_no, pgn_string=pgn_string)
    
@router.get("/get_best_move")
async def get_best_move(pgn_string: str, move_no: int):
    return await app.get_best_move(pgn_string=pgn_string, move_no=move_no)

@router.get("/get_best_moves")
async def getBestMoves(pgn_string: str):
    return await app.get_best_moves(pgn_string=pgn_string)