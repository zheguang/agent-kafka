#!/usr/bin/env python
import json
import logging

from fastmcp import FastMCP
from kafka import KafkaAdminClient

MCP_SERVER_NAME="kafka"

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(MCP_SERVER_NAME)

# Initialize MCP server
mcp = FastMCP(MCP_SERVER_NAME)

def create_kafka_client() -> KafkaAdminClient:
    logger.info("Creating Kakfa client connection")

    try:
        kafka = KafkaAdminClient(bootstrap_servers=["localhost:9092"], client_id="mcp-kafka")
        # Test the connection
        cluster_metadata = kafka.describe_cluster()
        logger.info(f"Successfully connected to Kafka server version {cluster_metadata}")
        return kafka
    except Exception as e:
        logger.error(f"Failed to connect to Kafka: {str(e)}")
        raise

# Initialize Kafka Client
kafka = create_kafka_client()

@mcp.tool()
async def list_topics() -> str:
    """List available Kafka topics"""
    result = kafka.list_topics()
    return as_json(result)

@mcp.tool()
async def create_topics(new_topic: str) -> str:
    """Create a new Kafka topic"""
    result = kafka.create_topics(new_topics=[new_topic])
    return as_json([result])

def as_json(result) -> str:
    # Convert newline-separated string to list and trim whitespace
    if isinstance(result, str):
        xs = [x.strip() for x in result.strip().split("\n")]
    else:
        xs = [result]
    return json.dumps(xs)

def run_stdio_server():
    mcp.run(transport="stdio")


if __name__ == "__main__":
    run_stdio_server()
