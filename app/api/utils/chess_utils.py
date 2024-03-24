import uuid

from app.db.mongo_client import ZuMongoClient


def generate_hex_uuid():
    """
    Generates a unique hex UUID.

    Returns:
        str: A string representation of a hex UUID.
    """
    return uuid.uuid4().hex


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
        await ZuMongoClient.insert_one(col="pgn_data", insert_data=pgn_dict)
        print("PGN data saved successfully.")
    except Exception as e:
        print(f"Failed to save PGN data to DB. Error: {e}")
