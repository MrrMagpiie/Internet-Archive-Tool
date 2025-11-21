def clear_layout(layout):
    """Helper to remove all widgets from a layout."""
    if layout is not None:
        while layout.count():
            item = layout.takeAt(0)
            if item.widget() is not None:
                item.widget().setParent(None)