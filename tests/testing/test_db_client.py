import pytest
from pytest_mock import MockerFixture
from sqlalchemy.engine import Engine
from sqlalchemy.exc import ResourceClosedError

from fast_alchemy.persistence.database import Database, _session
from fast_alchemy.testing.db_client import TestDatabase
from tests.testing.factories_stub import UserFactory, AccountFactory, Base, User
import sqlalchemy_utils


@pytest.fixture
def db():
    return Database("sqlite://")

def test_db_engine(db):
    test_db = TestDatabase(db=db)
    assert test_db.engine.url == db.url
    assert isinstance(test_db.engine, Engine)

def test_load_factory(db):
    test_db = TestDatabase(db=db, factories_module="tests.testing.factories_stub")
    assert test_db.factories == [AccountFactory, UserFactory]

def test_db_client_create_database(db, mocker:MockerFixture):
    create_database = mocker.patch.object(sqlalchemy_utils, "create_database")
    mocker.patch.object(sqlalchemy_utils, "database_exists", return_value=False)
    metadata = mocker.Mock()
    test_db = TestDatabase(db=db)
    test_db.create_test_database(metadata)
    metadata.create_all.assert_called()
    create_database.assert_called_with(db.url)

def test_db_client_release_resources(db, mocker: MockerFixture):
    drop_database = mocker.patch.object(sqlalchemy_utils, "drop_database")
    test_db = TestDatabase(db=db)
    engine = mocker.patch.object(test_db, "engine")
    connection = mocker.patch.object(test_db, "connection")
    test_db.__del__()
    engine.dispose.assert_called()
    connection.close.assert_called()
    drop_database.assert_called_with(db.url)

def test_start_test_session(db):
    test_db = TestDatabase(db=db, factories_module="tests.testing.factories_stub")
    test_db.create_test_database(Base.metadata)
    with test_db.start_test_session() as session:
        assert _session.get() == session
        UserFactory(name="Pierre")
        session.commit()
        users = session.query(User).all()
        assert len(users) == 1
        assert users[0].name == "Pierre"
    assert _session.get() is None
    with test_db.start_test_session() as session:
        assert _session.get() == session
        users = session.query(User).all()
        assert len(users) == 0
    assert _session.get() is None
    test_db.__del__()
    with pytest.raises(ResourceClosedError):
        UserFactory(name="Roger")