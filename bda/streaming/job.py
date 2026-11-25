"""Kafka-to-model-to-MongoDB/HDFS Structured Streaming pipeline."""

from __future__ import annotations

import os

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import ArrayType, DoubleType, StringType, StructField, StructType

from features.schemas import TRANSACTION_SCHEMA
from ml.score import FraudScorer
from storage.mongo_writer import MongoAlertWriter


BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:29092")
CHECKPOINT_DIR = os.getenv("CHECKPOINT_DIR", "/checkpoints/fraud-scoring")
HDFS_OUTPUT = os.getenv("HDFS_OUTPUT", "hdfs://namenode:9000/data/scored")
MODEL_DIR = os.getenv("MODEL_DIR", "/app/ml/artifacts")
SCORE_SCHEMA = StructType([
    StructField("risk_score", DoubleType(), False),
    StructField("risk_level", StringType(), False),
    StructField("ml_score", DoubleType(), False),
    StructField("anomaly_score", DoubleType(), False),
    StructField("rule_score", DoubleType(), False),
    StructField("triggered_rules", ArrayType(StringType()), False),
])


def get_spark() -> SparkSession:
    return (
        SparkSession.builder.appName("RealTimeFraudDetection")
        .config("spark.sql.session.timeZone", "UTC")
        .getOrCreate()
    )


def build_transactions(spark: SparkSession) -> DataFrame:
    raw = (
        spark.readStream.format("kafka")
        .option("kafka.bootstrap.servers", BOOTSTRAP_SERVERS)
        .option("subscribe", "transactions")
        .option("startingOffsets", "latest")
        .option("maxOffsetsPerTrigger", 1000)
        .load()
    )
    parsed = raw.select(
        F.from_json(F.col("value").cast("string"), TRANSACTION_SCHEMA).alias("event")
    ).select("event.*")

    return (
        parsed.filter(
            F.col("txn_id").isNotNull()
            & F.col("account_id").isNotNull()
            & F.col("timestamp").isNotNull()
            & (F.col("amount") > 0)
            & (F.col("amount") < 100000)
        )
        .withWatermark("timestamp", "1 hour")
        .dropDuplicates(["txn_id", "timestamp"])
        .withColumn("amount_to_account_avg", F.coalesce("amount_to_account_avg", F.lit(1.0)))
        .withColumn("txn_count_60m", F.coalesce("txn_count_60m", F.lit(1)))
        .withColumn("failed_logins_before_txn", F.coalesce("failed_logins_before_txn", "failed_logins", F.lit(0)))
        .withColumn("is_new_device", F.coalesce("is_new_device", F.lit(False)))
        .withColumn("failed_logins", F.coalesce("failed_logins", F.lit(0)))
        .withColumn("ip_reputation", F.coalesce("ip_reputation", F.lit(0.0)))
        .withColumn("vpn_flag", F.coalesce("vpn_flag", F.lit(False)))
        .withColumn("blacklisted_ip", F.coalesce("blacklisted_ip", F.lit(False)))
        .withColumn("merchant_risk", F.coalesce("merchant_risk", F.lit(0.0)))
    )


def score_batch(
    batch: DataFrame,
    batch_id: int,
    scorer: FraudScorer,
    alert_writer: MongoAlertWriter,
) -> None:
    scored_events = []
    for row in batch.toLocalIterator():
        event = row.asDict(recursive=True)
        scores = scorer.score(event)
        scored_events.append({**event, **scores})

    if not scored_events:
        return

    alert_writer.write_batch(scored_events)
    event_schema = StructType(batch.schema.fields + SCORE_SCHEMA.fields)
    scored_batch = batch.sparkSession.createDataFrame(scored_events, schema=event_schema)
    (
        scored_batch
        .withColumn("event_date", F.to_date("timestamp"))
        .write.mode("overwrite")
        .partitionBy("event_date")
        .parquet(f"{HDFS_OUTPUT}/batch_id={batch_id}")
    )
    print(f"Batch {batch_id}: scored and persisted {len(scored_events)} transactions")


def main() -> None:
    spark = get_spark()
    scorer = FraudScorer(MODEL_DIR)
    alert_writer = MongoAlertWriter(
        os.getenv("MONGO_URI", "mongodb://mongo:27017"),
        os.getenv("MONGO_DB", "fraud"),
    )
    transactions = build_transactions(spark)

    query = (
        transactions.writeStream
        .foreachBatch(
            lambda batch, batch_id: score_batch(
                batch, batch_id, scorer, alert_writer
            )
        )
        .outputMode("append")
        .option("checkpointLocation", CHECKPOINT_DIR)
        .start()
    )
    query.awaitTermination()


if __name__ == "__main__":
    main()
