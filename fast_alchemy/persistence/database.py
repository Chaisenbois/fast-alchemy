import contextlib

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from .context import _session


class Database:
    def __init__(self, url, autoflush=False, autocommit=False, **engine_options):
        self.url = url
        self.engine = create_engine(self.url, **engine_options)
        self._session_factory = sessionmaker(bind=self.engine, autoflush=autoflush, autocommit=autocommit)

    @property
    def session(self) -> Session:
        session = _session.get()
        assert session ,"Make sure to use the session within a session context"
        return session

    @contextlib.contextmanager
    def session_ctx(self):
        assert self._session_factory is not None, "Make sure that the database middleware is " \
                                                  "installed and well configured"
        session = self._session_factory()
        token = _session.set(session)
        try:
            yield
        finally:
            session.close()
            _session.reset(token)

