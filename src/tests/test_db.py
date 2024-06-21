from mock import patch, MagicMock

from sqlalchemy.exc import OperationalError, DataError


@patch("robot_cleaner.api.clean.add_execution")
def test_execute_cleaning_on_exception_max_tries(
    m_execute_cleaning: MagicMock, app, caplog, database
):
    """
    Test db calls giving up after 3 retries on operational errors.
    """
    m_execute_cleaning.side_effect = OperationalError(
        None, None, "Connection Failure",
    )

    app.test_client().post(
        "/tibber-developer-test/enter-path",
        json={"start": {"x": 1, "y": 2}, "commands": []},
    )

    assert m_execute_cleaning.call_count == 3
    assert "Backing off execute_cleaning(...)" in caplog.records[0].message # noqa
    assert "Backing off execute_cleaning(...)" in caplog.records[1].message # noqa
    assert (
        "Giving up execute_cleaning(...) after 3 tries"
        in caplog.records[2].message
    )


@patch("robot_cleaner.api.clean.add_execution")
def test_no_retries_on_non_operational_errors(
    m_execute_cleaning: MagicMock, app, database
):
    """
    Test db calls giving up after one try on non operational errors.
    """
    m_execute_cleaning.side_effect = DataError(
        None, None, "Value out of range",
    )

    app.test_client().post(
        "/tibber-developer-test/enter-path",
        json={"start": {"x": 1, "y": 2}, "commands": []},
    )
    assert m_execute_cleaning.call_count == 1
