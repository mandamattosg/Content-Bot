from app.database.base import Base

__all__ = ["Base"]


def __getattr__(name: str):
    if name in {"SessionLocal", "engine"}:
        from app.database.session import SessionLocal, engine

        return {"SessionLocal": SessionLocal, "engine": engine}[name]
    raise AttributeError(name)
