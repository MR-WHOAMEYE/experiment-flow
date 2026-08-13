"""
Seed 10,000 synthetic clean_records and run US-3.1 EXPLAIN ANALYZE benchmark.
"""
import json
import random
from sqlalchemy import text
from db.connection import get_connection
from db.benchmark import benchmark_query, save_benchmark

DATASET_ID = "benchmark-dataset-10k"

def seed_and_run():
    with get_connection() as conn:
        conn.execute(text("DELETE FROM clean_records WHERE dataset_id = :ds"), {"ds": DATASET_ID})
        conn.execute(text("DROP INDEX IF EXISTS idx_clean_records_dataset_key"))

        print("Seeding 10,000 synthetic records into clean_records...")
        rows = [
            {
                "dataset_id": DATASET_ID,
                "unique_key": f"KEY-{i:06d}",
                "fields": json.dumps({"user_id": i, "score": round(random.random() * 100, 2), "group": "A" if i % 2 == 0 else "B"}),
            }
            for i in range(10000)
        ]

        insert_sql = text("""
            INSERT INTO clean_records (dataset_id, unique_key, fields)
            VALUES (:dataset_id, :unique_key, :fields)
        """)
        conn.execute(insert_sql, rows)
        print("10,000 rows inserted.")

        print("Running US-3.1 EXPLAIN ANALYZE benchmark...")
        query_label = "Dataset & Key Lookup Speedup"
        query_sql = f"SELECT * FROM clean_records WHERE dataset_id = '{DATASET_ID}' AND unique_key = 'KEY-005000'"
        index_sql = "CREATE INDEX IF NOT EXISTS idx_clean_records_dataset_key ON clean_records (dataset_id, unique_key)"

        res = benchmark_query(conn, query_label, query_sql, index_sql)
        print(f"\n--- Benchmark Results for '{res.query_label}' ---")
        print(f"Before Index Execution Time: {res.before_ms:.2f} ms (Cost: {res.before_plan_cost})")
        print(f"After Index Execution Time:  {res.after_ms:.2f} ms (Cost: {res.after_plan_cost})")
        print(f"Speedup Multiplier:          {res.speedup_multiplier}x faster!")

        save_benchmark(conn, res)
        print("Benchmark result successfully recorded in query_benchmarks table.")

if __name__ == "__main__":
    seed_and_run()
