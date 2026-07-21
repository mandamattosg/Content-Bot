from abc import ABC, abstractmethod

from app.models.signal import Signal


class Collector(ABC):
    @abstractmethod
    def collect(self) -> list[Signal]:
        raise NotImplementedError
