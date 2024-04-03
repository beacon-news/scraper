#!/bin/bash

docker run --name scraper --rm -v $PWD/../investigations/articles_and_configs/scrape_configs:/configs --network host \
  scraper -c /configs/abc_news/world.yaml -l1 --store mongodb --notifier redis_streams