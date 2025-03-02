from abc import ABC, abstractmethod
from collections import defaultdict
from collections.abc import Callable, Iterator
from copy import deepcopy
from dataclasses import dataclass, field
from enum import Enum
from typing import Generic, TypeVar

from validator.adapter import Adapter, adapt

T = TypeVar("T")


class EventType(Enum):
    GET = "get"
    UPDATE = "update"
    DELETE = "delete"
    ADD = "add"
    REMOVE = "remove"


@dataclass(frozen=True)
class Event:
    event_type: EventType
    key: str
    kwargs: dict[str, object] = field(default_factory=dict, kw_only=True)


class Observer(ABC):
    @abstractmethod
    def update(self, observable: "Observable", event: Event) -> None:
        """Update the observer with an event.

        Args:
            observable: The observable instance.
            event: The event that occurred.
        """
        pass


class Observable(ABC):
    _observers: dict[EventType, list[Observer]]

    def __init__(self) -> None:
        """Initialize the observable with an empty list of observers."""
        self._observers = defaultdict(list)

    @property
    def observers(self) -> dict[EventType, list[Observer]]:
        """Get a copy of the observers dictionary.

        Returns:
            A deep copy of the observers dictionary.
        """
        return deepcopy(self._observers)

    def attach(self, event_type: EventType, observer: Observer) -> None:
        """Attach an observer to an event type.

        Args:
            event_type: The type of event to observe.
            observer: The observer to attach.
        """
        self._observers[event_type].append(observer)

    def detach(self, event_type: EventType, observer: Observer) -> None:
        """Detach an observer from an event type.

        Args:
            event_type: The type of event to stop observing.
            observer: The observer to detach.
        """
        self._observers[event_type].remove(observer)

    def notify(self, event: Event) -> None:
        """Notify all observers of an event.

        Args:
            event: The event to notify observers about.
        """
        for observer in self._observers[event.event_type]:
            observer.update(self, event)


class observable:  # noqa: N801
    def __init__(
        self, fget: Callable, fset: Callable | None = None, fdel: Callable | None = None
    ) -> None:
        """Initialize the observable property.

        Args:
            fget: The getter function.
            fset: The setter function.
            fdel: The deleter function.
        """
        self.fget = fget
        self.fset = fset
        self.fdel = fdel

    def __get__(self, instance, owner) -> object:  # noqa: ANN001
        """Get the value of the property and notify observers.

        Args:
            instance: The instance of the class.
            owner: The owner class.

        Returns:
            The value of the property.
        """
        value = self.fget(instance)
        event: Event = Event(EventType.GET, self.fget.__name__, kwargs={"value": value})
        self.notify(instance=instance, event=event)
        return value

    def __set__(self, instance, new_value) -> None:  # noqa: ANN001
        """Set the value of the property and notify observers.

        Args:
            instance: The instance of the class.
            new_value: The new value to set.
        """
        old_value = self.fget(instance)
        self.fset(instance, new_value)  # type: ignore[misc]
        event: Event = Event(
            EventType.UPDATE,
            self.fset.__name__,  # type: ignore[union-attr]
            kwargs={"old_value": old_value, "new_value": new_value},
        )
        self.notify(instance=instance, event=event)

    def __delete__(self, instance) -> None:  # noqa: ANN001
        """Delete the property and notify observers.

        Args:
            instance: The instance of the class.
        """
        value = self.fget(instance)
        self.fdel(instance)  # type: ignore[misc]
        event: Event = Event(EventType.DELETE, self.fdel.__name__, kwargs={"value": value})  # type: ignore[union-attr]
        self.notify(instance=instance, event=event)

    def notify(self, instance: Observable | Adapter, event: Event) -> None:
        """Notify observers of an event.

        Args:
            instance: The instance of the class.
            event: The event to notify observers about.
        """
        observable: Observable | None = adapt(instance, Observable)
        if observable:
            observable.notify(event=event)

    def getter(self, fget: Callable) -> "observable":
        """Create a new observable property with a getter.

        Args:
            fget: The getter function.

        Returns:
            A new observable property.
        """
        return type(self)(fget=fget, fset=self.fset, fdel=self.fdel)

    def setter(self, fset: Callable) -> "observable":
        """Create a new observable property with a setter.

        Args:
            fset: The setter function.

        Returns:
            A new observable property.
        """
        return type(self)(fget=self.fget, fset=fset, fdel=self.fdel)

    def deleter(self, fdel: Callable) -> "observable":
        """Create a new observable property with a deleter.

        Args:
            fdel: The deleter function.

        Returns:
            A new observable property.
        """
        return type(self)(fget=self.fget, fset=self.fset, fdel=fdel)


class ObservableList(Observable, Generic[T]):
    def __init__(self, initial: list[T] | None = None) -> None:
        """Initialize the observable list.

        Args:
            initial: The initial list of items.
        """
        super().__init__()
        self._list = initial if initial is not None else []

    def append(self, item: T) -> None:
        """Append an item to the list and notify observers.

        Args:
            item: The item to append.
        """
        self._list.append(item)
        event = Event(EventType.ADD, "append", kwargs={"item": item})
        self.notify(event)

    def remove(self, item: T) -> None:
        """Remove an item from the list and notify observers.

        Args:
            item: The item to remove.
        """
        self._list.remove(item)
        event = Event(EventType.REMOVE, "remove", kwargs={"item": item})
        self.notify(event)

    def __getitem__(self, index: int) -> T:
        """Get an item from the list and notify observers.

        Args:
            index: The index of the item.

        Returns:
            The item at the specified index.
        """
        item = self._list[index]
        event = Event(EventType.GET, "getitem", kwargs={"index": index, "item": item})
        self.notify(event)
        return item

    def __setitem__(self, index: int, value: T) -> None:
        """Set an item in the list and notify observers.

        Args:
            index: The index of the item.
            value: The new value to set.
        """
        old_value = self._list[index]
        self._list[index] = value
        event = Event(
            EventType.UPDATE,
            "setitem",
            kwargs={"index": index, "old_value": old_value, "new_value": value},
        )
        self.notify(event)

    def __delitem__(self, index: int) -> None:
        """Delete an item from the list and notify observers.

        Args:
            index: The index of the item.
        """
        item = self._list.pop(index)
        event = Event(EventType.DELETE, "delitem", kwargs={"index": index, "item": item})
        self.notify(event)

    def __iter__(self) -> Iterator[T]:
        """Return an iterator over the list.

        Returns:
            An iterator over the list.
        """
        return iter(self._list)

    def __len__(self) -> int:
        """Return the length of the list.

        Returns:
            The length of the list.
        """
        return len(self._list)

    def __repr__(self) -> str:
        """Return a string representation of the list.

        Returns:
            A string representation of the list.
        """
        return repr(self._list)
