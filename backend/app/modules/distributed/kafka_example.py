"""Kafka producer/consumer code (kafka-python — pure Python protocol
implementation, no compiled client library). Needs an actual Kafka broker
reachable at KAFKA_BOOTSTRAP_SERVERS; a broker needs either Zookeeper or
KRaft mode plus persistent storage, so run it via the `kafka` service in
docker-compose.yml at the repo root rather than standing one up manually.

Sketches the shape this platform would use Kafka for: RAG document ingestion
as a stream (upload -> "documents.ingested" topic -> a consumer group does
chunking/embedding off the request path) instead of the synchronous
in-request pipeline app/modules/rag/router.py currently runs.
"""

import json
import os

BOOTSTRAP_SERVERS = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
TOPIC = "documents.ingested"


def check_available() -> None:
    try:
        import kafka  # noqa: F401
    except ImportError as exc:
        raise RuntimeError("kafka-python isn't installed (`pip install kafka-python`).") from exc


def publish_document_ingested(doc_id: str, collection: str, source: str) -> None:
    check_available()
    from kafka import KafkaProducer

    producer = KafkaProducer(
        bootstrap_servers=BOOTSTRAP_SERVERS,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    )
    try:
        producer.send(TOPIC, {"doc_id": doc_id, "collection": collection, "source": source})
        producer.flush(timeout=10)
    finally:
        producer.close()


def consume_document_ingested(max_messages: int = 10) -> list[dict]:
    check_available()
    from kafka import KafkaConsumer

    consumer = KafkaConsumer(
        TOPIC,
        bootstrap_servers=BOOTSTRAP_SERVERS,
        group_id="omniai-rag-indexer",
        value_deserializer=lambda v: json.loads(v.decode("utf-8")),
        auto_offset_reset="earliest",
        consumer_timeout_ms=5000,
    )
    messages = []
    try:
        for record in consumer:
            messages.append(record.value)
            if len(messages) >= max_messages:
                break
    finally:
        consumer.close()
    return messages
