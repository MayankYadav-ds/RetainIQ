from sqlalchemy import Engine, create_engine, text


def build_engine(url: str) -> Engine:
    options = {"check_same_thread": False, "timeout": 2} if url.startswith("sqlite") else {}
    return create_engine(url, connect_args=options, pool_pre_ping=True)


def probe(engine: Engine) -> bool:
    with engine.connect() as connection:
        value: object = connection.execute(text("SELECT 1")).scalar_one()
        return isinstance(value, int) and value == 1
