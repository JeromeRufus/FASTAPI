from sqlalchemy.orm import Session


def distinct_values(db: Session, column) -> list[str]:
    """Returns the distinct, non-null values currently stored in a column."""
    return [row[0] for row in db.query(column).distinct().all() if row[0]]