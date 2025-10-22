#!/usr/bin/env python
import json
import logging

from fastmcp import FastMCP
from kafka import KafkaAdminClient
from kafka.admin import ConfigResource, ConfigResourceType
from pydantic import BaseModel, Field
from typing import Annotated, Literal

MCP_SERVER_NAME="kafka"

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
log = logging.getLogger(MCP_SERVER_NAME)

# Initialize MCP server
mcp = FastMCP(MCP_SERVER_NAME)

def create_admin_client() -> KafkaAdminClient:
    log.info("Creating Kakfa client connection")

    try:
        admin = KafkaAdminClient(bootstrap_servers=["localhost:9092"], client_id="mcp-kafka")
        # Test the connection
        cluster_metadata = admin.describe_cluster()
        log.info(f"Successfully connected to Kafka server version {cluster_metadata}")
        return admin
    except Exception as e:
        log.error(f"Failed to connect to Kafka: {str(e)}")
        raise

# Initialize admin client
admin = create_admin_client()

class ConfigResourceInput(BaseModel):
    """Pydantic model representing a Kakfa ConfigResource"""
    resource_type: Annotated[
        Literal["BROKER", "TOPIC"], 
        Field(description="Type of resource: BROKER or TOPIC")
    ]

    name: Annotated[str, Field(description="Resource name (broker ID integer or Kakfa topic name string)")]

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
            name=self.name,
            configs=self.configs
        )

@mcp.tool()
async def list_topics() -> str:
    """List available Kafka topics"""
    result = admin.list_topics()
    return as_json(result)

@mcp.tool()
async def create_topics(new_topics: list[str]) -> str:
    """Create new Kafka topics"""
    result = admin.create_topics(new_topics=new_topics)
    return as_json(result)

@mcp.tool()
async def describe_cluster() -> str:
    """Describe cluster-wide metadata such as the list of brokers, the controller ID, and the cluster ID."""
    result = admin.describe_cluster()
    return as_json(result)

@mcp.tool()
async def describe_configs(resources: list[ConfigResourceInput]) -> list[dict]:
    """Describe configuration for one or more Kafka resources."""
    config_resources = [r.to_config_resource() for r in resources]
    result = admin.describe_configs(config_resources=config_resources)

    # convert result to list of dicts
    resources = [r.to_object()['resources'] for r in result]
    return resources


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
