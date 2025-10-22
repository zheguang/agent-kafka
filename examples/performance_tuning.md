# Tune Kafka configurations for performance

- Prompt: 
```
Show me throughput related configuration parameters for my brokers.
```
- Agent:
```
Final model: result='log.flush.interval.messages: 9223372036854775807
log.flush.interval.ms: 
log.flush.offset.checkpoint.interval.ms: 60000
log.roll.jitter.hours: 0
log.segment.bytes: 1073741824
log.segment.delete.delay.ms: 60000
log.retention.bytes: -1
log.roll.hours: 168
log.flush.start.offset.checkpoint.interval.ms: 60000
log.roll.jitter.ms: '
```

- Log:
```
[10/22/25 14:10:27] INFO     Starting MCP server 'kafka' with transport 'stdio'                          server.py:1445
2025-10-22 14:10:27,330 - mcp.server.lowlevel.server - INFO - Processing request of type ListToolsRequest
2025-10-22 14:10:30,684 - mcp.server.lowlevel.server - INFO - Processing request of type CallToolRequest
All run entries:
tool_call_id='vMu6HMBdX' name='describe_configs' arguments='{"resources": [{"resource_type": "BROKER", "name": "1", "configs": {"log.flush.interval.messages": "", "log.flush.interval.ms": "", "log.flush.start.offset.checkpoint.interval.ms": "", "log.flush.offset.checkpoint.interval.ms": "", "log.retention.bytes": "", "log.segment.bytes": "", "log.segment.ms": "", "log.roll.hours": "", "log.roll.jitter.hours": "", "log.roll.jitter.ms": "", "log.segment.delete.delay.ms": ""}}]}' object='entry' type='function.call' created_at=datetime.datetime(2025, 10, 22, 3, 11, 31, 336298, tzinfo=TzInfo(UTC)) completed_at=None id='fc_019a09e67c08768494c8ebb67d215b0f'

tool_call_id='vMu6HMBdX' result='[{"type": "text", "text": "Output validation error: [{\'error_code\': 0, \'error_message\': \'\', \'resource_type\': 4, \'resource_name\': \'1\', \'config_entries\': [{\'config_names\': \'log.flush.interval.messages\', \'config_value\': \'9223372036854775807\', \'read_only\': False, \'config_source\': 5, \'is_sensitive\': False, \'config_synonyms\': []}, {\'config_names\': \'log.flush.interval.ms\', \'config_value\': None, \'read_only\': False, \'config_source\': 5, \'is_sensitive\': False, \'config_synonyms\': []}, {\'config_names\': \'log.flush.offset.checkpoint.interval.ms\', \'config_value\': \'60000\', \'read_only\': True, \'config_source\': 5, \'is_sensitive\': False, \'config_synonyms\': []}, {\'config_names\': \'log.roll.jitter.hours\', \'config_value\': \'0\', \'read_only\': True, \'config_source\': 5, \'is_sensitive\': False, \'config_synonyms\': []}, {\'config_names\': \'log.segment.bytes\', \'config_value\': \'1073741824\', \'read_only\': False, \'config_source\': 4, \'is_sensitive\': False, \'config_synonyms\': []}, {\'config_names\': \'log.segment.delete.delay.ms\', \'config_value\': \'60000\', \'read_only\': False, \'config_source\': 5, \'is_sensitive\': False, \'config_synonyms\': []}, {\'config_names\': \'log.retention.bytes\', \'config_value\': \'-1\', \'read_only\': False, \'config_source\': 5, \'is_sensitive\': False, \'config_synonyms\': []}, {\'config_names\': \'log.roll.hours\', \'config_value\': \'168\', \'read_only\': True, \'config_source\': 5, \'is_sensitive\': False, \'config_synonyms\': []}, {\'config_names\': \'log.flush.start.offset.checkpoint.interval.ms\', \'config_value\': \'60000\', \'read_only\': True, \'config_source\': 5, \'is_sensitive\': False, \'config_synonyms\': []}, {\'config_names\': \'log.roll.jitter.ms\', \'config_value\': None, \'read_only\': False, \'config_source\': 5, \'is_sensitive\': False, \'config_synonyms\': []}]}] is not of type \'object\'"}]' object='entry' type='function.result' created_at=None completed_at=Unset() id=None

content='{"result": "log.flush.interval.messages: 9223372036854775807\\nlog.flush.interval.ms: \\nlog.flush.offset.checkpoint.interval.ms: 60000\\nlog.roll.jitter.hours: 0\\nlog.segment.bytes: 1073741824\\nlog.segment.delete.delay.ms: 60000\\nlog.retention.bytes: -1\\nlog.roll.hours: 168\\nlog.flush.start.offset.checkpoint.interval.ms: 60000\\nlog.roll.jitter.ms: \\n"}' object='entry' type='message.output' created_at=datetime.datetime(2025, 10, 22, 3, 11, 33, 516484, tzinfo=TzInfo(UTC)) completed_at=datetime.datetime(2025, 10, 22, 3, 11, 34, 791867, tzinfo=TzInfo(UTC)) id='msg_019a09e6848c712797e09efb2bd4208b' agent_id='ag_019a09e6731570e1813da50014253207' model='mistral-small-latest' role='assistant'

Final model: result='log.flush.interval.messages: 9223372036854775807\nlog.flush.interval.ms: \nlog.flush.offset.checkpoint.interval.ms: 60000\nlog.roll.jitter.hours: 0\nlog.segment.bytes: 1073741824\nlog.segment.delete.delay.ms: 60000\nlog.retention.bytes: -1\nlog.roll.hours: 168\nlog.flush.start.offset.checkpoint.interval.ms: 60000\nlog.roll.jitter.ms: \n'
```
