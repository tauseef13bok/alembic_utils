import pytest
from alembic.util import AutogenerateDiffsDetected
from sqlalchemy import text

from alembic_utils.pg_function import PGFunction
from alembic_utils.pg_view import PGView
from alembic_utils.replaceable_entity import register_entities
from alembic_utils.testbase import run_alembic_command

to_upper = PGFunction(
    schema="public",
    signature="to_upper(some_text text)",
    definition="""
        returns text
        as
        $$ select upper(some_text) $$ language SQL;
        """,
)

TEST_VIEW_before = PGView(
    schema="public",
    signature="testExample",
    definition="select feature_name from information_schema.sql_features",
)
TEST_VIEW_after = PGView(
    schema="public",
    signature="testExample",
    definition="select feature_name, is_supported from information_schema.sql_features",
)


def test_create_and_drop(engine) -> None:
    """Test that the alembic current command does not error"""
    # Runs with no error
    up_sql = to_upper.to_sql_statement_create()
    down_sql = to_upper.to_sql_statement_drop()

    # Testing that the following two lines don't raise
    with engine.begin() as connection:
        connection.execute(up_sql)
        result = connection.execute(text("select public.to_upper('hello');")).fetchone()
        assert result[0] == "HELLO"
        connection.execute(down_sql)
        assert True


def test_check_diff_create(engine) -> None:
    register_entities([TEST_VIEW_before])

    with pytest.raises(AutogenerateDiffsDetected) as e_info:
        run_alembic_command(engine, "check", {})

    exp = (
        "New upgrade operations detected: "
        "[('create_entity', 'PGView: public.testExample', "
        '\'CREATE VIEW "public"."testExample" AS select feature_name from information_schema.sql_features;\')]'
    )
    assert e_info.value.args[0] == exp
