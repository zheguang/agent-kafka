# Agentic Kafka

Turn operational data into analytical insights, at real time. Brought to you by the Agent Kafka.

## Install dependencies
```
pip install mistralai mcp[cli] griffe kafka-python duckdb
```

## Run
1. Start a Kafka cluster
2. Connect to the cluster and start the agent
```
MISTRAL_API_KEY=<Your LLM API Key> python agents/agent_mistral.py
```

## Use cases
See `examples/`
- Performance tuning
- Real-time analytics
