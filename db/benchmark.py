"""
Database Query Benchmarking Module -- US-3.1 (ADR-003)

Responsibilities:
  1. Parse PostgreSQL `EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)` output into execution time (ms) and total planner cost.
  2. Run query before index creation, create index, run query after index creation.
  3. Save results into the `query_benchmarks` database table for reporting and dashboard visualization.

References: ADR-003, prompt.md US-3.1
"""
import re
from dataclasses import dataclass
from typing import Dict, Any

from sqlalchemy import text
from sqlalchemy.engine import Connection

from ingestion.logger import get_logger

log = get_logger(__name__)

_COST_RE = re.compile(r"cost=\d+\.\d+\.\.(\d+\.\d+)")
_EXEC_TIME_RE = re.compile(r"Execution Time:\s*(\d+\.\d+)\s*ms")


@dataclass
class BenchmarkResult:
    """Benchmark outcome for a single query optimization run."""
    query_label: str
    before_ms: float
    after_ms: float
    before_plan_cost: float
    after_plan_cost: float

    @property
    def speedup_multiplier(self) -> float:
        """Return how many times faster the query runs after indexing."""
        return round(self.before_ms / max(self.after_ms, 0.001), 2)


def parse_explain_output(explain_text: str) -> Dict[str, float]:
    """
    Parse text output of EXPLAIN ANALYZE.

    Args:
        explain_text: Raw string output from EXPLAIN ANALYZE.

    Returns:
        dict with keys: execution_time_ms (float), total_cost (float).

    Raises:
        ValueError: If cost or execution time patterns are not found.
    """
    cost_match = _COST_RE.search(explain_text)
    exec_match = _EXEC_TIME_RE.search(explain_text)

    if not cost_match or not exec_match:
        raise ValueError(f"Could not parse EXPLAIN output. Content:\n{explain_text}")

    return {
        "total_cost": float(cost_match.group(1)),
        "execution_time_ms": float(exec_match.group(1)),
    }


def benchmark_query(
    conn: Connection,
    query_label: str,
    query_sql: str,
    index_sql: str,
) -> BenchmarkResult:
    """
    Benchmark a query before and after creating a database index.

    Args:
        conn:        Active SQLAlchemy Connection.
        query_label: Descriptive name for the query benchmark.
        query_sql:   SQL SELECT statement to benchmark.
        index_sql:   SQL DDL statement to create the index (e.g. CREATE INDEX IF NOT EXISTS ...).

    Returns:
        BenchmarkResult populated with before/after timings and plan costs.
    """
    log.info("benchmark_query started", extra={"label": query_label})

    explain_prefix = "EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT) "

    # 1. EXPLAIN before index
    res_before = conn.execute(text(explain_prefix + query_sql))
    lines_before = "\n".join(r[0] for r in res_before.fetchall())
    parsed_before = parse_explain_output(lines_before)

    # 2. Create index
    log.info("Creating index for benchmark", extra={"index_sql": index_sql})
    conn.execute(text(index_sql))

    # 3. EXPLAIN after index
    res_after = conn.execute(text(explain_prefix + query_sql))
    lines_after = "\n".join(r[0] for r in res_after.fetchall())
    parsed_after = parse_explain_output(lines_after)

    result = BenchmarkResult(
        query_label=query_label,
        before_ms=parsed_before["execution_time_ms"],
        after_ms=parsed_after["execution_time_ms"],
        before_plan_cost=parsed_before["total_cost"],
        after_plan_cost=parsed_after["total_cost"],
    )

    log.info(
        "benchmark_query complete",
        extra={
            "label": query_label,
            "before_ms": result.before_ms,
            "after_ms": result.after_ms,
            "speedup": f"{result.speedup_multiplier}x",
        },
    )
    return result


def save_benchmark(conn: Connection, result: BenchmarkResult) -> None:
    """
    Insert benchmark results into query_benchmarks table.

    Args:
        conn:   Active SQLAlchemy Connection.
        result: BenchmarkResult instance to persist.
    """
    insert_sql = text(
        """
        INSERT INTO query_benchmarks (query_label, before_ms, after_ms, before_plan_cost, after_plan_cost)
        VALUES (:query_label, :before_ms, :after_ms, :before_plan_cost, :after_plan_cost)
        """
    )
    conn.execute(
        insert_sql,
        {
            "query_label": result.query_label,
            "before_ms": result.before_ms,
            "after_ms": result.after_ms,
            "before_plan_cost": result.before_plan_cost,
            "after_plan_cost": result.after_plan_cost,
        },
    )
    log.info("save_benchmark stored in DB", extra={"label": result.query_label})
