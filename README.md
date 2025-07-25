# Azure Monitor + @distributed_trace

📦 Azure Monitor integration with OpenTelemetry via `@distributed_trace` annotation 🔍 

## Configuration
Create a `.env` file in the project root — see `.env.sample` for reference.

## Kusto Queries

### 1. Retrieve traces from the last hour
```kusto
traces
| where timestamp > ago(1h)
| where message contains "Sample"
| project timestamp, message, customDimensions
| order by timestamp desc
```

### 2. Logs sent by AzureMonitorLogExporter
```kusto
traces
| where timestamp > ago(1h)
| where message contains "Processing" or message contains "Processed"
| project timestamp, message, severityLevel, customDimensions
| order by timestamp desc
```

### 3. Spans sent by AzureMonitorTraceExporter

| `SpanKind` | Azure Monitor Table | Description                             |
| ---------- | ------------------- | --------------------------------------- |
| `INTERNAL` | `traces`            | Background operations or internal logic |
| `SERVER`   | `requests`          | Incoming HTTP or RPC requests           |
| `CLIENT`   | `dependencies`      | Outgoing calls to external services     |
| `PRODUCER` | `dependencies`      | Messages sent to queues/topics          |
| `CONSUMER` | `dependencies`      | Messages received from queues/topics    |

#### Combined logs and spans
```kusto
union traces, dependencies, requests, exceptions
| where timestamp > ago(1h)
| where message contains "Processing" or message contains "Processed"
| project timestamp, itemType, message, operation_Name, severityLevel, customDimensions
| order by timestamp desc
```

#### Aggregate logs by severity
```kusto
traces
| where timestamp > ago(1h)
| summarize Count = count() by severityLevel
| order by severityLevel
```

#### Aggregate spans by operation name
```kusto
traces
| where timestamp > ago(1h)
| summarize Count = count() by operation_Name
| order by Count desc
```

#### Span extraction (dependencies, requests, traces)
```kusto
union dependencies, requests, traces
| where timestamp > ago(1h)
| project timestamp, itemType, operation_Name, id, duration, customDimensions
| order by timestamp desc
```

#### View INTERNAL span
```kusto
traces
| where timestamp > ago(1h)
| where message contains "Internal operation span"
| project timestamp, message, customDimensions
```

#### View SERVER span
```kusto
requests
| where timestamp > ago(1h)
| where name == "server_span"
| project timestamp, name, operation_Name, customDimensions
```

#### View CLIENT span
```kusto
dependencies
| where timestamp > ago(1h)
| where name == "client_span"
| project timestamp, name, target, operation_Name
```

#### View PRODUCER & CONSUMER spans
```kusto
dependencies
| where timestamp > ago(1h)
| where name in ("producer_span", "consumer_span")
| project timestamp, name, operation_Name, target
```
