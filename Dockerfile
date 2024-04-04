FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt requirements.txt

RUN pip3 install -r requirements.txt --no-cache-dir

RUN useradd app --create-home --shell /bin/bash
USER app

VOLUME /scrape_conf

ENV CACHE_TYPE=redis
ENV STORE_TYPE=mongodb
ENV NOTIFIER_TYPE=redis_streams
ENV SCRAPER_ARTICLE_LIMIT=2
ENV SCRAPER_PROCESSES=1
ENV SCRAPER_CONFIG_FILE=

COPY --chown=app:app . .

ENTRYPOINT ["python3", "src/main.py"]
