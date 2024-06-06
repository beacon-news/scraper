FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt requirements.txt

RUN pip3 install -r requirements.txt --no-cache-dir

RUN useradd app --create-home --shell /bin/bash
USER app

VOLUME /scrape_conf

COPY --chown=app:app . .

ENTRYPOINT ["python3", "src/main.py"]
