import pytest

from starterkit.observer import EventType, Observable, ObservableList, Observer, observable


class TestObserver(Observer):
    def __init__(self):
        self.events = []

    def update(self, observable, event):
        self.events.append(event)


class TestObservable(Observable):
    def __init__(self):
        super().__init__()
        self._value = 0

    @observable
    def value(self):
        return self._value

    @value.setter  # type: ignore[no-redef]
    def value(self, new_value):
        self._value = new_value


@pytest.fixture
def setup_observable():
    observable = TestObservable()
    observer = TestObserver()
    observable.attach(EventType.UPDATE, observer)
    observable.attach(EventType.GET, observer)
    return observable, observer


def test_attach_observer(setup_observable):
    observable, observer = setup_observable
    assert len(observable.observers[EventType.UPDATE]) == 1


def test_detach_observer(setup_observable):
    observable, observer = setup_observable
    observable.detach(EventType.UPDATE, observer)
    assert len(observable.observers[EventType.UPDATE]) == 0


def test_notify_observer(setup_observable):
    observable, observer = setup_observable
    observable.value = 10
    assert len(observer.events) == 1
    assert observer.events[0].event_type == EventType.UPDATE
    assert observer.events[0].kwargs["new_value"] == 10


def test_observable_getter(setup_observable):
    observable, observer = setup_observable
    observable._value = 5
    assert observable.value == 5
    assert len(observer.events) == 1
    assert observer.events[0].event_type == EventType.GET
    assert observer.events[0].kwargs["value"] == 5


def test_observable_setter(setup_observable):
    observable, observer = setup_observable
    observable.value = 20
    assert observable.value == 20
    assert len(observer.events) == 2
    assert observer.events[0].event_type == EventType.UPDATE
    assert observer.events[0].kwargs["new_value"] == 20


@pytest.fixture
def setup_observable_list():
    observable = ObservableList[int]()
    observer = TestObserver()
    observable.attach(EventType.ADD, observer)
    observable.attach(EventType.REMOVE, observer)
    observable.attach(EventType.UPDATE, observer)
    observable.attach(EventType.DELETE, observer)
    observable.attach(EventType.GET, observer)
    return observable, observer


def test_observable_list(setup_observable_list):
    observable, observer = setup_observable_list

    observable.append(1)
    assert len(observer.events) == 1
    assert observer.events[0].event_type == EventType.ADD
    assert observer.events[0].kwargs["item"] == 1

    observable[0] = 42
    assert len(observer.events) == 2
    assert observer.events[-1].event_type == EventType.UPDATE
    assert observer.events[-1].kwargs["new_value"] == 42

    observable.remove(42)
    assert len(observer.events) == 3
    assert observer.events[-1].event_type == EventType.REMOVE
    assert observer.events[-1].kwargs["item"] == 42
