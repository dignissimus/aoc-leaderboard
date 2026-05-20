# AoC 2025 Leaderboard

A simple FastAPI interface to submit Advent of Code solutions and inputs, with automated execution via Judge0.

## Setup

### Generate token

```bash
./generate-token.sh
```
This will create `secrets/token`. All pages require `?token=YOUR_TOKEN` to load.

### Start judge0

```bash
./start-judge0.sh
```
This script builds a custom Docker image (including GFortran and custom Rust) and automatically registers the new languages in the Judge0 database (IDs 101 and 102).

### Dependencies

```bash
uv sync
```

# Run application

```bash
./run.sh
# OR
uv run main.py
```
The application will be available at `http://localhost:8000/?token=YOUR_TOKEN`.

## Dayta storage

SQLite Database: `aoc.db`
Inputs: `data/{normalised-name}/input/day-xx`
Solutions: `data/{normalised-name}/solutions/{uuid}.extension`
Secrets: `secrets/token`
