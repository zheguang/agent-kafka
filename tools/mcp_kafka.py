#!/usr/bin/env python
import asyncio
import duckdb
import json
import logging

from mcp.server.fastmcp import FastMCP
from kafka import KafkaAdminClient
from kafka.admin import ConfigResource, ConfigResourceType
from pydantic import BaseModel, Field
from typing import Annotated, Literal, Optional

MCP_SERVER_NAME="mcp_kafka"
DB_FILE="db-kafka.tmp"

KAFKA_BOOTSTRAP_SERVERS=["localhost:9092"]

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
log = logging.getLogger(MCP_SERVER_NAME)

# Initialize MCP server
mcp = FastMCP(MCP_SERVER_NAME)

def create_database() -> duckdb.DuckDBPyConnection:
    db = duckdb.connect(DB_FILE)
    db.execute("INSTALL tributary FROM community; LOAD tributary;")
    return db

# Initialize database for persistence
db = create_database()

def create_admin_client() -> KafkaAdminClient:
    log.info("Creating Kakfa client connection")

    try:
        admin = KafkaAdminClient(bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS, client_id="mcp-kafka")
        # Test the connection
        cluster_metadata = admin.describe_cluster()
        log.info(f"Successfully connected to Kafka server version {cluster_metadata}")
        return admin
    except Exception as e:
        log.error(f"Failed to connect to Kafka: {str(e)}")
        raise

# Initialize admin client
admin = create_admin_client()

# Initialize schema cache, hardcoded for now
schemas = { 
    "lineitem": {
        "timestamp": "varchar",
        "order_id": "varchar",
        "part_id": "varchar"
    }
}

class ConfigResourceInput(BaseModel):
    """Pydantic model representing a Kakfa ConfigResource"""
    resource_type: Annotated[
        Literal["BROKER", "TOPIC"], 
        Field(description="Type of resource: BROKER or TOPIC")
    ]

    broker_node_id_or_topic_name: Annotated[int | str, Field(description="Resource name (broker node ID integer or Kakfa topic name string)")]

    configs: Annotated[
        dict[str, str] | None,
        Field(default=None, description="Configuration key-value pairs")
    ] = None

    def to_config_resource(self) -> ConfigResource:
        """Convert to kafka.admin.ConfigResource"""
        resource_type_map = {
            "BROKER": ConfigResourceType.BROKER,
            "TOPIC": ConfigResourceType.TOPIC,
        }
        return ConfigResource(
            resource_type=resource_type_map[self.resource_type],
            name=self.broker_node_id_or_topic_name,
            configs=self.configs
        )

@mcp.tool()
async def list_topics() -> str:
    """List available Kafka topics"""
    result = await asyncio.get_event_loop().run_in_executor(None, admin.list_topics)
    return as_json(result)

@mcp.tool()
async def create_topics(new_topics: list[str]) -> str:
    """Create new Kafka topics"""
    result = await asyncio.get_event_loop().run_in_executor(None, admin.create_topics, new_topics)
    return as_json(result)

@mcp.tool()
async def describe_cluster() -> str:
    """Describe cluster-wide metadata such as the list of brokers, the controller ID, and the cluster ID."""
    result = await asyncio.get_event_loop().run_in_executor(None, admin.describe_cluster)
    return as_json(result)

@mcp.tool()
async def describe_configs(resource_input: list[ConfigResourceInput]) -> list[dict]:
    """Describe configuration for one or more Kafka resources."""
    config_resources = [r.to_config_resource() for r in resource_input]
    result = await asyncio.get_event_loop().run_in_executor(None, admin.describe_configs, config_resources)

    # convert result to list of dicts
    resources = [r.to_object()['resources'] for r in result]
    return resources

@mcp.tool()
def describe_topic_schema(topic: str) -> dict:
    """Describe the schema of a Kafka topic's messages."""
    return schemas[topic]

@mcp.tool()
async def create_topic_table(topic: str) -> bool:
    """Create a table view over the topic's messages."""
    with db.cursor() as cursor:
        cursor.execute(f"""
            CREATE VIEW IF NOT EXISTS {topic}_raw AS
                SELECT *
                EXCLUDE message,
                decode(message)::json AS message
                FROM tributary_scan_topic('{topic}', "bootstrap.servers" := '{",".join(KAFKA_BOOTSTRAP_SERVERS)}');
        """)

        schema = schemas[topic]
        projection = ','.join([f"(message ->> '$.{attr}'::{type_name}) AS {attr}" for attr, type_name in schema.items()])

        view = f"""
            CREATE VIEW IF NOT EXISTS {topic} AS
                SELECT {projection}
                FROM {topic}_raw
        """
        log.debug(view)
        cursor.execute(view)
        return True

@mcp.tool()
async def query_topic_table(query: str) -> str:
    """Query the topic table as SQL and return results as JSON.

    Returns a JSON array of query results that can be passed to generate_plot().
    Each row is represented as a list of values.

    Args:
        query: SQL query to execute against the topic table

    Returns:
        JSON string containing array of rows, where each row is a list of values
    """
    log.info(f"Running query: {query}")
    with db.cursor() as cursor:
        results = cursor.sql(query).fetchall()
        # Convert to JSON string for agent consumption
        return json.dumps([list(row) for row in results])

def as_json(result, transform=lambda x: x) -> str:
    # Convert newline-separated string to list and trim whitespace
    if isinstance(result, str):
        xs = [transform(x).strip() for x in result.strip().split("\n")]
    elif isinstance(result, list):
        xs = [transform(x) for x in result]
    else:
        xs = [result]
    return json.dumps(xs)

def run_stdio_server():
    mcp.run(transport="stdio")

if __name__ == "__main__":
    run_stdio_server()
