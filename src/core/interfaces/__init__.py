from abc import ABC, abstractmethod
from typing import Any

class ChannelSender(ABC):
    @abstractmethod
    async def send(self, recipient: str, subject: str, message: str) -> None:
        pass

class MessageBroker(ABC):
    @abstractmethod
    async def consume(self, callback):
        pass

class EmailSender(ABC):
    @abstractmethod
    async def send(self, to: str, subject: str, body: str):
        pass

class SmsSender(ABC):
    @abstractmethod
    async def send(self, to: str, message: str):
        pass

class DisplayNotifier(ABC):
    @abstractmethod
    async def notify(self, user_id: str, message: str):
        pass

class IdempotencyCache(ABC):
    @abstractmethod
    async def is_processed(self, event_id: str) -> bool:
        pass
    @abstractmethod
    async def mark_processed(self, event_id: str):
        pass