from fastapi import APIRouter, Depends
from fastapi_jwt_auth import AuthJWT

from app.api.controllers import app

router = APIRouter()


@router.get("/delete_this_route")
async def delete_this_route(
    Authorize: AuthJWT = Depends(),
):
    res: dict = await app.delete_this_route()
    return res


@router.post("/pgn")
async def pgn(
    pgn_string: str,
):
    # Assuming there's a utility function to validate PGN format
    is_valid_pgn = await app.validate_pgn_format(pgn_string)
    if is_valid_pgn:
        pgn_dict = app.pgn_to_dict(pgn_string)

        moves_dict = app.moves_to_dict(pgn_dict["Moves"][0])
        print(moves_dict)
        pgn_dict["Moves"] = moves_dict
        save_result = await app.save_pgn_to_db(pgn_dict)
        if save_result:
            pgn_dict.pop("_id", None)  # Remove ObjectId which is not serializable
            return {"message": "PGN saved successfully", "data": pgn_dict}
        else:
            return {"message": "Failed to save PGN", "status": "error"}, 500

    else:
        return {"message": "Invalid PGN format", "status": "error"}, 400
