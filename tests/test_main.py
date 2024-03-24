import logging.config

import pytest
from fastapi.testclient import TestClient

import logConfig
from app.main import app

logging.config.dictConfig(logConfig.config)
logger = logging.getLogger(__name__)

client = TestClient(app)


@pytest.mark.order(1)
def test_read_main():
    logger.info("Checking Server")
    response = client.get("/ping")
    logger.debug("GET /ping")
    logger.debug("Response: " + str(response.json()))
    assert response.status_code == 200
    assert response.json() == {"ping": "pong"}
