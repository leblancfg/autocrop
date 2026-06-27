def by_slow_marker(item):
    return item.get_closest_marker("slow") is not None


def pytest_collection_modifyitems(items):
    items.sort(key=by_slow_marker)
