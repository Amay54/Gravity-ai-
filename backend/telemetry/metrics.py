from typing import Any

from loguru import logger


class MetricsCollector:
    """
    Collects performance counters, execution durations, and resource utilization.
    """

    def __init__(self) -> None:
        self.agent_runs: dict[str, list[float]] = {}
        self.tool_runs: dict[str, list[float]] = {}
        self.total_tokens_consumed: int = 0
        self.failure_count: int = 0

    def record_agent_duration(self, agent_name: str, duration_ms: float) -> None:
        logger.debug(f"Telemetry: Agent '{agent_name}' completed in {duration_ms:.2f}ms")
        runs = self.agent_runs.setdefault(agent_name, [])
        runs.append(duration_ms)

    def record_tool_duration(self, tool_name: str, duration_ms: float) -> None:
        logger.debug(f"Telemetry: Tool '{tool_name}' completed in {duration_ms:.2f}ms")
        runs = self.tool_runs.setdefault(tool_name, [])
        runs.append(duration_ms)

    def record_tokens(self, count: int) -> None:
        self.total_tokens_consumed += count
        logger.debug(
            f"Telemetry: Added {count} tokens to counter. Total: {self.total_tokens_consumed}"
        )

    def record_failure(self) -> None:
        self.failure_count += 1

    def get_summary(self) -> dict[str, Any]:
        """
        Synthesizes aggregate counters into a single telemetry payload.
        """
        summary = {
            "total_tokens": self.total_tokens_consumed,
            "failure_count": self.failure_count,
            "agent_performance": {},
            "tool_performance": {},
        }

        # Calculate averages for agents
        for name, runs in self.agent_runs.items():
            summary["agent_performance"][name] = {
                "invocations": len(runs),
                "avg_duration_ms": sum(runs) / len(runs) if runs else 0.0,
            }

        # Calculate averages for tools
        for name, runs in self.tool_runs.items():
            summary["tool_performance"][name] = {
                "invocations": len(runs),
                "avg_duration_ms": sum(runs) / len(runs) if runs else 0.0,
            }

        return summary


# Global singleton metrics collector
telemetry_metrics = MetricsCollector()
