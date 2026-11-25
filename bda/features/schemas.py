from pyspark.sql.types import (
    BooleanType,
    DoubleType,
    IntegerType,
    StringType,
    StructField,
    StructType,
    TimestampType,
)


TRANSACTION_SCHEMA = StructType([
    StructField("txn_id", StringType(), False),
    StructField("account_id", StringType(), False),
    StructField("amount", DoubleType(), False),
    StructField("currency", StringType(), True),
    StructField("timestamp", TimestampType(), False),
    StructField("merchant_id", StringType(), True),
    StructField("channel", StringType(), True),
    StructField("device_id", StringType(), True),
    StructField("lat", DoubleType(), True),
    StructField("lon", DoubleType(), True),
    StructField("is_new_device", BooleanType(), True),
    StructField("failed_logins", IntegerType(), True),
    StructField("ip_reputation", DoubleType(), True),
    StructField("vpn_flag", BooleanType(), True),
    StructField("blacklisted_ip", BooleanType(), True),
    StructField("merchant_risk", DoubleType(), True),
    StructField("amount_to_account_avg", DoubleType(), True),
    StructField("txn_count_60m", IntegerType(), True),
    StructField("failed_logins_before_txn", IntegerType(), True),
])

DEVICE_SCHEMA = StructType([
    StructField("device_id", StringType(), False),
    StructField("account_id", StringType(), False),
    StructField("os", StringType(), True),
    StructField("is_new_device", BooleanType(), True),
    StructField("timestamp", TimestampType(), False),
])

LOCATION_SCHEMA = StructType([
    StructField("account_id", StringType(), False),
    StructField("txn_id", StringType(), True),
    StructField("lat", DoubleType(), True),
    StructField("lon", DoubleType(), True),
    StructField("ip_country", StringType(), True),
    StructField("city", StringType(), True),
    StructField("timestamp", TimestampType(), False),
])

MERCHANT_SCHEMA = StructType([
    StructField("merchant_id", StringType(), False),
    StructField("category", StringType(), True),
    StructField("risk_score", DoubleType(), True),
    StructField("country", StringType(), True),
])

BEHAVIOUR_SCHEMA = StructType([
    StructField("account_id", StringType(), False),
    StructField("txn_id", StringType(), True),
    StructField("login_time", TimestampType(), True),
    StructField("session_length", DoubleType(), True),
    StructField("failed_logins", IntegerType(), True),
    StructField("typing_speed", DoubleType(), True),
    StructField("timestamp", TimestampType(), False),
])

NETWORK_SCHEMA = StructType([
    StructField("account_id", StringType(), False),
    StructField("txn_id", StringType(), True),
    StructField("ip_reputation", DoubleType(), True),
    StructField("vpn_flag", BooleanType(), True),
    StructField("blacklisted_ip", BooleanType(), True),
    StructField("timestamp", TimestampType(), False),
])
