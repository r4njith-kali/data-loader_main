
"""Transactional PostgreSQL bulk loading utilities."""

from collections.abc import Sequence

import pandas as pd
from sqlalchemy import MetaData, Table
from sqlalchemy.dialects.postgresql import insert


def upsert_dataframe(
    df: pd.DataFrame,
    engine,
    table_name: str,
    schema: str,
    conflict_columns: Sequence[str],
    batch_size: int = 1000,
    update_existing: bool = False,
) -> int:
    """Insert or upsert records using database uniqueness constraints.

    The destination table must already exist and have a matching
    unique constraint or primary key for conflict_columns.
    """
    if batch_size <= 0:
        raise ValueError("batch_size must be positive")

    if not conflict_columns:
        raise ValueError("conflict_columns cannot be empty")

    if df.empty:
        return 0

    metadata = MetaData()
    table = Table(
        table_name,
        metadata,
        schema=schema,
        autoload_with=engine,
    )

    unknown_columns = set(df.columns) - set(table.columns.keys())
    if unknown_columns:
        raise ValueError(
            f"Unknown destination columns: {sorted(unknown_columns)}"
        )

    missing_keys = set(conflict_columns) - set(df.columns)
    if missing_keys:
        raise ValueError(
            f"Missing conflict columns: {sorted(missing_keys)}"
        )

    if df[list(conflict_columns)].isna().any().any():
        raise ValueError("Conflict columns cannot contain null values")

    records = df.to_dict(orient="records")

    # Deduplicate within the incoming batch.
    unique_df = df.drop_duplicates(
        subset=list(conflict_columns),
        keep="last",
    )
    records = unique_df.to_dict(orient="records")

    affected = 0

    with engine.begin() as connection:
        for offset in range(0, len(records), batch_size):
            batch = records[offset:offset + batch_size]

            statement = insert(table).values(batch)

            if update_existing:
                update_columns = {
                    column: statement.excluded[column]
                    for column in df.columns
                    if column not in conflict_columns
                }

                if update_columns:
                    statement = statement.on_conflict_do_update(
                        index_elements=list(conflict_columns),
                        set_=update_columns,
                    )
                else:
                    statement = statement.on_conflict_do_nothing(
                        index_elements=list(conflict_columns)
                    )
            else:
                statement = statement.on_conflict_do_nothing(
                    index_elements=list(conflict_columns)
                )

            result = connection.execute(statement)
            affected += result.rowcount

    return affected
