# Real-Time Fraud Detection System

A Docker-based big-data pipeline for generating and scoring financial transactions in near real time.

## Architecture

The system follows a four-stage flow:

1. The producer publishes transactions and available transaction features to Kafka.
2. Spark Structured Streaming validates and parses the transaction stream.
3. The trained ML models and rule engine score each micro-batch.
4. MongoDB stores suspicious alerts; HDFS stores all scored transactions as partitioned Parquet.

## Project layout

```text
fraud-bda/
├── docker-compose.yml
├── data/
├── producers/
├── streaming/
├── features/
├── ml/
├── rules/
├── storage/
├── dashboard/
└── tests/
```

## Quick start

```bash
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe data\generate_data.py
.\.venv\Scripts\python.exe ml\train.py --csv data\transactions.csv --artifacts ml\artifacts
docker compose up --build
```

The dashboard is available at `http://localhost:8501`. Kafka is exposed on `localhost:9092`, MongoDB on `localhost:27017`, Spark UI on `localhost:8080`, and the Hadoop NameNode UI on `http://localhost:9870`.

In another terminal, publish transactions after the services are ready:

```bash
.\.venv\Scripts\python.exe producers\kafka_producer.py --speed 10 --count 100
```

The `spark-job` Compose service submits `streaming/job.py` to Spark and writes its streaming checkpoint to a named volume. The producer uses the shared offline feature engineering code before publishing so trained and streaming model inputs align. Stop the pipeline with `docker compose down`; keep volumes to preserve MongoDB/HDFS data and the checkpoint. To reset offsets/checkpoint state, remove the Compose volumes intentionally with `docker compose down -v`.

## Topics

- `transactions`
- `device-events`
- `location-events`
- `behaviour-logs`
- `network-events`
- `merchants`
- `feedback`

All account-based events use `account_id` as the Kafka key so events for an account remain ordered.
The current scoring job consumes `transactions`; the generated transaction message carries the available behavioral and network feature fields. The companion topics are reserved for extending the enrichment pipeline.

## Local development

Run unit tests:

```bash
.\.venv\Scripts\python.exe -m pytest -m "not integration"
```

Replay synthetic events directly from a terminal:

```bash
.\.venv\Scripts\python.exe producers\kafka_producer.py --speed 10 --count 100
```

Check that the job is running and inspect its logs:

```bash
docker compose ps
docker compose logs -f spark-job
```

Look for `Loaded trained fraud model artifacts` and `scored and persisted ... transactions` in the Spark job logs. If artifacts are missing, the scorer explicitly warns that it is using the deterministic baseline. Suspicious and high-risk alerts appear on the dashboard; all scored events are written under HDFS `/data/scored`, partitioned by batch and event date.

Start the Streamlit dashboard:

```bash
.\.venv\Scripts\streamlit.exe run dashboard\app.py
```

## Detection policy

The final risk score is:

`0.55 * ML probability + 0.20 * anomaly score + 0.25 * rule score`

Scores below `0.35` are Legitimate, scores from `0.35` to `0.75` are Suspicious, and scores above `0.75` are High Risk. Thresholds and weights should be tuned using validation cost, not accuracy alone.
