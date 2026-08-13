"""
Tests for db/benchmark.py -- US-3.1 (ADR-003)

Gherkin ACs covered:
  Given a table with 10,000+ clean_records
  When a common analytical query is executed before and after adding a database index
  Then the platform measures query execution time using EXPLAIN ANALYZE
  And records the before/after timing in the query_benchmarks table demonstrating measurable speedup
"""
import pytest
from db.benchmark import parse_explain_output, benchmark_query, save_benchmark, BenchmarkResult


SAMPLE_EXPLAIN_OUTPUT = """
Seq Scan on clean_records  (cost=0.00..314.00 rows=10000 width=108) (actual time=0.015..12.450 rows=10000 loops=1)
  Filter: (dataset_id = 'test-dataset'::text)
Planning Time: 0.120 ms
Execution Time: 13.850 ms
"""

SAMPLE_EXPLAIN_INDEXED = """
Index Scan using idx_clean_records_dataset_key on clean_records  (cost=0.28..8.30 rows=100 width=108) (actual time=0.020..0.450 rows=100 loops=1)
  Index Cond: (dataset_id = 'test-dataset'::text)
Planning Time: 0.080 ms
Execution Time: 0.520 ms
"""


class TestExplainParser:
    def test_parse_execution_time_and_cost(self):
        result = parse_explain_output(SAMPLE_EXPLAIN_OUTPUT)
        assert pytest.approx(result["execution_time_ms"], 0.01) == 13.85
        assert pytest.approx(result["total_cost"], 0.01) == 314.00

    def test_parse_indexed_explain_output(self):
        result = parse_explain_output(SAMPLE_EXPLAIN_INDEXED)
        assert pytest.approx(result["execution_time_ms"], 0.01) == 0.52
        assert pytest.approx(result["total_cost"], 0.01) == 8.30

    def test_parse_malformed_text_raises_value_error(self):
        with pytest.raises(ValueError, match="Could not parse EXPLAIN output"):
            parse_explain_output("invalid plain text without cost or execution time")


class TestBenchmarkExecution:
    def test_benchmark_query_calculates_speedup(self, mocker):
        mock_conn = mocker.MagicMock()

        # Return unindexed EXPLAIN result first, then indexed EXPLAIN result
        mock_res1 = mocker.MagicMock()
        mock_res1.fetchall.return_value = [(l,) for l in SAMPLE_EXPLAIN_OUTPUT.strip().split("\n")]

        mock_res2 = mocker.MagicMock()
        mock_res2.fetchall.return_value = [(l,) for l in SAMPLE_EXPLAIN_INDEXED.strip().split("\n")]

        mock_conn.execute.side_effect = [
            mock_res1,            # EXPLAIN ANALYZE before
            mocker.MagicMock(),   # CREATE INDEX
            mock_res2,            # EXPLAIN ANALYZE after
        ]

        result = benchmark_query(
            conn=mock_conn,
            query_label="Dataset Key Lookup",
            query_sql="SELECT * FROM clean_records WHERE dataset_id = 'abc'",
            index_sql="CREATE INDEX idx_clean_records_dataset_key ON clean_records (dataset_id, unique_key)",
        )

        assert isinstance(result, BenchmarkResult)
        assert result.query_label == "Dataset Key Lookup"
        assert pytest.approx(result.before_ms, 0.01) == 13.85
        assert pytest.approx(result.after_ms, 0.01) == 0.52
        assert result.speedup_multiplier > 20.0

    def test_save_benchmark_executes_insert(self, mocker):
        mock_conn = mocker.MagicMock()
        res = BenchmarkResult(
            query_label="Dataset Key Lookup",
            before_ms=13.85,
            after_ms=0.52,
            before_plan_cost=314.0,
            after_plan_cost=8.30,
        )

        save_benchmark(mock_conn, res)
        mock_conn.execute.assert_called_once()
        _sql, params = mock_conn.execute.call_args.args
        assert params["query_label"] == "Dataset Key Lookup"
        assert params["before_ms"] == 13.85
        assert params["after_ms"] == 0.52
