FROM python:3.8-slim
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential gcc curl  \
    && apt-get clean

RUN pip install --upgrade pip

COPY ./requirements.txt /app/requirements.txt

RUN python -m pip install --no-cache-dir -r /app/requirements.txt


COPY ./ /app

WORKDIR /app
ENV PYTHONPATH=/app

CMD ["uvicorn", "app.main:app", "--proxy-headers","--forwarded-allow-ips","*","--host","0.0.0.0","--port","80"]

HEALTHCHECK --start-period=10s --interval=30s --timeout=5s CMD curl -f http://localhost:/ping | grep pong || exit 1
