# Docker MongoDB

Local MongoDB runs through `docker-compose.yml`.

## Requirements

```bash
docker --version
docker-compose --version
```

This repo uses `docker-compose` by default. If WSL cannot find it but Docker Desktop has Compose, run Make targets with:

```bash
make COMPOSE="/mnt/c/Program\ Files/Docker/Docker/resources/bin/docker-compose.exe" mongo-up
```

## Start MongoDB

```bash
cd /home/hp/dev/work/bni-bions-sentiment-analysis
make mongo-up
make mongo-status
```

MongoDB binds to localhost:

```env
MONGODB_URI=mongodb://localhost:27017
MONGODB_DATABASE=bni_bions_sentiment
```

Inside Compose network, use `mongodb://mongo:27017`.

## Init behavior

On first volume creation, MongoDB runs scripts mounted at:

```txt
./db -> /docker-entrypoint-initdb.d:ro
```

Active init script:

```txt
db/mongo-init.js
```

It creates core collections, indexes, provider metadata, and seed keywords.

Named volume:

```txt
bni-bions-sentiment-analysis_mongo_data
```

Do not run `docker-compose down -v` unless you intend to delete MongoDB data.

## Shell

```bash
make mongo-shell
```

Useful checks:

```javascript
db.runCommand({ ping: 1 })
db.getCollectionNames()
db.social_items.getIndexes()
db.collector_providers.countDocuments()
db.keywords.countDocuments()
```

## Collector write path

Collectors write when `write=True` reaches `pipeline.storage.social_items.persist_social_items()`.

Default DB config is read from env by `apps/api/app/config.py`:

```env
MONGODB_URI=mongodb://localhost:27017
MONGODB_DATABASE=bni_bions_sentiment
```

Legacy `MONGODB_DB` remains accepted as fallback, but use `MONGODB_DATABASE` going forward.

## Stop

```bash
make mongo-down
```

Keeps named volume.

## Destroy local DB data

Dangerous. Only when you want a clean database:

```bash
docker-compose down -v
```

Then start again:

```bash
make mongo-up
```
