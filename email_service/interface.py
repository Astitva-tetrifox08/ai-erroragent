from abc import ABC, abstractmethod

class EmailReader(ABC):

    @abstractmethod
    def read_latest_email(self) -> str:
        pass

    @abstractmethod
    def read_latest_subject(self) -> str:
        pass
