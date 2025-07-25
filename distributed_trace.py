import os
import logging
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry._logs import set_logger_provider
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from azure.monitor.opentelemetry.exporter import (
    AzureMonitorTraceExporter,
    AzureMonitorLogExporter,
)
from azure.core.tracing.decorator import distributed_trace
from loguru import logger
from dotenv import load_dotenv
from opentelemetry.trace import SpanKind

# Load environment variables from .env file
load_dotenv()


# Loguru integration with OpenTelemetry
class InterceptHandler(logging.Handler):
    def emit(self, record):
        logger_opt = logger.opt(depth=6, exception=record.exc_info)
        logger_opt.log(record.levelname, record.getMessage())


def setup_azure_logging():
    """Setup Azure Monitor logging and tracing"""
    # Initialize providers
    logger_provider = LoggerProvider()
    set_logger_provider(logger_provider)

    tracer_provider = TracerProvider()
    trace.set_tracer_provider(tracer_provider)

    # Configure exporters
    connection_string = os.environ["APPLICATIONINSIGHTS_CONNECTION_STRING"]

    # Log exporter: exports application log records to Azure Monitor (Application Insights)
    log_exporter = AzureMonitorLogExporter.from_connection_string(connection_string)
    logger_provider.add_log_record_processor(BatchLogRecordProcessor(log_exporter))

    # Trace exporter: exports distributed tracing spans to Azure Monitor (Application Insights)
    # Target tables by span kind:
    #   SpanKind.SERVER   -> requests
    #   SpanKind.CLIENT   -> dependencies
    #   SpanKind.INTERNAL -> traces
    trace_exporter = AzureMonitorTraceExporter.from_connection_string(connection_string)
    tracer_provider.add_span_processor(BatchSpanProcessor(trace_exporter))

    # Setup Python logging handlers
    handler = LoggingHandler(level=logging.INFO, logger_provider=logger_provider)

    # Use Loguru and OpenTelemetry together
    logging.basicConfig(level=logging.INFO, handlers=[InterceptHandler(), handler])
    logging.getLogger().addHandler(handler)
    logging.getLogger().setLevel(logging.INFO)


def get_tracer(name=__name__):
    """Get tracer instance"""
    return trace.get_tracer(name)


# Sample usages of different SpanKind values
""" 
| `SpanKind` | Azure Monitor Table | Description                             |
| ---------- | ------------------- | --------------------------------------- |
| `INTERNAL` | `traces`            | Background operations or internal logic |
| `SERVER`   | `requests`          | Incoming HTTP or RPC requests           |
| `CLIENT`   | `dependencies`      | Outgoing calls to external services     |
| `PRODUCER` | `dependencies`      | Messages sent to queues/topics          |
| `CONSUMER` | `dependencies`      | Messages received from queues/topics    |
 """


def sample_spans():
    tracer = get_tracer("sample_module")
    with tracer.start_as_current_span("internal_span", kind=SpanKind.INTERNAL):
        logger.info("Internal operation span")
    with tracer.start_as_current_span("server_span", kind=SpanKind.SERVER):
        logger.info("Server handling request span")
    with tracer.start_as_current_span("client_span", kind=SpanKind.CLIENT):
        logger.info("Client making external call span")
    with tracer.start_as_current_span("producer_span", kind=SpanKind.PRODUCER):
        logger.info("Producing a message span")
    with tracer.start_as_current_span("consumer_span", kind=SpanKind.CONSUMER):
        logger.info("Consuming a message span")


@distributed_trace
def process_data(payload):
    """Example function with distributed tracing"""
    tracer = get_tracer()
    with tracer.start_as_current_span("process_data"):
        logger.info(f"Processing: {payload}")
        # Business logic here
        return f"Processed: {payload}"


def main():
    # Initialize Azure Monitor logging and tracing
    setup_azure_logging()

    result = process_data("sample payload")
    print(f"Result: {result}")

    # demonstrate SpanKind usage
    sample_spans()


if __name__ == "__main__":
    main()
