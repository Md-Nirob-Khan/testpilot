"""SQLite persistence for engine comparisons."""

import json
import os
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence


@dataclass(frozen=True)
class EngineRun:
    """Store one engine's result for a function in a comparison."""

    function_name: str
    engine_name: str
    status: str
    error: str | None = None
    line_percent: float | None = None
    branch_percent: float | None = None
    mutation_score: float | None = None
    wrong_test_count: int | None = None
    wrong_test_status: str | None = None
    wall_clock_seconds: float | None = None
    estimated_cost_usd: float | None = None
    test_code: str | None = None


@dataclass(frozen=True)
class RunSummary:
    """Summarize one persisted dashboard run."""

    run_id: int
    created_at: str
    source_name: str
    function_names: tuple[str, ...]


@dataclass(frozen=True)
class StoredRun:
    """Represent a run and all its persisted engine results."""

    summary: RunSummary
    results: tuple[EngineRun, ...]


class RunHistory:
    """Persist comparison runs and generated suites in a SQLite database."""

    def __init__(self, database_path: Path | None = None) -> None:
        """Initialize history at an explicit path or configured local database."""
        configured_path = os.environ.get(
            "TESTPILOT_DB_PATH",
            "testpilot_runs.sqlite3",
        )
        self.database_path = Path(database_path or configured_path).expanduser()
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def save_run(
        self,
        source_name: str,
        function_names: Sequence[str],
        results: Sequence[EngineRun],
    ) -> int:
        """Save a comparison and every generated or failed engine result."""
        created_at = datetime.now(timezone.utc).isoformat()
        with self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO runs (created_at, source_name, function_names_json)
                VALUES (?, ?, ?)
                """,
                (created_at, source_name, json.dumps(list(function_names))),
            )
            run_id = int(cursor.lastrowid)
            connection.executemany(
                """
                INSERT INTO engine_runs (
                    run_id, function_name, engine_name, status, error,
                    line_percent, branch_percent, mutation_score,
                    wrong_test_count, wrong_test_status, wall_clock_seconds,
                    estimated_cost_usd, test_code
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        run_id,
                        result.function_name,
                        result.engine_name,
                        result.status,
                        result.error,
                        result.line_percent,
                        result.branch_percent,
                        result.mutation_score,
                        result.wrong_test_count,
                        result.wrong_test_status,
                        result.wall_clock_seconds,
                        result.estimated_cost_usd,
                        result.test_code,
                    )
                    for result in results
                ],
            )
        return run_id

    def list_runs(self, limit: int = 50) -> list[RunSummary]:
        """Return the newest run summaries."""
        if isinstance(limit, bool) or not isinstance(limit, int) or limit < 1:
            raise ValueError("History limit must be a positive integer")
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT run_id, created_at, source_name, function_names_json
                FROM runs
                ORDER BY run_id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [
            RunSummary(
                run_id=row["run_id"],
                created_at=row["created_at"],
                source_name=row["source_name"],
                function_names=tuple(json.loads(row["function_names_json"])),
            )
            for row in rows
        ]

    def get_run(self, run_id: int) -> StoredRun:
        """Return a run with all generated test suites and metrics."""
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT run_id, created_at, source_name, function_names_json
                FROM runs
                WHERE run_id = ?
                """,
                (run_id,),
            ).fetchone()
            if row is None:
                raise KeyError(f"Run {run_id} does not exist")
            result_rows = connection.execute(
                """
                SELECT function_name, engine_name, status, error, line_percent,
                       branch_percent, mutation_score, wrong_test_count,
                       wrong_test_status, wall_clock_seconds,
                       estimated_cost_usd, test_code
                FROM engine_runs
                WHERE run_id = ?
                ORDER BY result_id
                """,
                (run_id,),
            ).fetchall()

        summary = RunSummary(
            run_id=row["run_id"],
            created_at=row["created_at"],
            source_name=row["source_name"],
            function_names=tuple(json.loads(row["function_names_json"])),
        )
        results = tuple(EngineRun(**dict(result_row)) for result_row in result_rows)
        return StoredRun(summary, results)

    def _connect(self) -> sqlite3.Connection:
        """Open a row-addressable connection with foreign keys enabled."""
        connection = sqlite3.connect(self.database_path, timeout=30)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def _initialize(self) -> None:
        """Create the run and result tables when they do not exist."""
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS runs (
                    run_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    source_name TEXT NOT NULL,
                    function_names_json TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS engine_runs (
                    result_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id INTEGER NOT NULL REFERENCES runs(run_id)
                        ON DELETE CASCADE,
                    function_name TEXT NOT NULL,
                    engine_name TEXT NOT NULL,
                    status TEXT NOT NULL,
                    error TEXT,
                    line_percent REAL,
                    branch_percent REAL,
                    mutation_score REAL,
                    wrong_test_count INTEGER,
                    wrong_test_status TEXT,
                    wall_clock_seconds REAL,
                    estimated_cost_usd REAL,
                    test_code TEXT
                );
                """
            )
