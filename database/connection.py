from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import Engine, create_engine, event, inspect
from sqlalchemy.engine import make_url
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.schema import CreateColumn

from config import DATABASE_URL


class Base(DeclarativeBase):
    pass


def build_engine(database_url: str = DATABASE_URL) -> Engine:
    connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
    url = make_url(database_url)
    if url.drivername.startswith("sqlite") and url.database not in (None, ":memory:"):
        Path(url.database).expanduser().parent.mkdir(parents=True, exist_ok=True)

    engine = create_engine(url, connect_args=connect_args)
    if url.drivername.startswith("sqlite"):

        @event.listens_for(engine, "connect")
        def enable_foreign_keys(dbapi_connection: object, _: object) -> None:
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    return engine


engine = build_engine()
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


def initialize_database(target_engine: Engine = engine) -> None:
    from database.models import Employee, Student

    Base.metadata.create_all(target_engine)
    legacy_profile_columns = {
        Student: (
            "admission_number",
            "date_of_birth",
            "email",
            "phone",
            "address",
            "guardian_name",
            "guardian_contact",
            "course",
            "department",
            "branch",
            "academic_year",
            "current_semester",
            "section",
            "admission_date",
            "enrollment_status",
            "profile_image_path",
        ),
        Employee: (
            "work_email",
            "work_phone",
            "joining_date",
            "employment_status",
            "reporting_manager",
            "emergency_contact",
            "skills",
            "certifications",
            "profile_image_path",
        ),
    }

    with target_engine.begin() as connection:
        preparer = target_engine.dialect.identifier_preparer
        for model, column_names in legacy_profile_columns.items():
            existing = {column["name"] for column in inspect(connection).get_columns(model.__tablename__)}
            for column_name in column_names:
                if column_name in existing:
                    continue
                column = model.__table__.c[column_name]
                definition = str(CreateColumn(column).compile(dialect=target_engine.dialect))
                connection.exec_driver_sql(
                    f"ALTER TABLE {preparer.quote(model.__tablename__)} ADD COLUMN {definition}"
                )

    admission_index = next(
        index
        for index in Student.__table__.indexes
        if index.name == "uq_students_admission_number"
    )
    admission_index.create(target_engine, checkfirst=True)


@contextmanager
def session_scope(factory: sessionmaker[Session] = SessionLocal) -> Iterator[Session]:
    session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()