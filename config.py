import os
from contextvars import ContextVar
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, scoped_session, sessionmaker

ROOT = os.path.dirname(os.path.abspath(__file__))

engine = create_engine(os.environ.get("ASCARIS_DB", f"sqlite:///{ROOT}/instance/test2.db"))
# one session per request: the app sets request_scope for each request and removes the session after it
request_scope = ContextVar("request_scope", default=None)
session = scoped_session(sessionmaker(engine), scopefunc=request_scope.get)
Base = declarative_base()
