def clear_layout(layout):
    """
    Recursively removes all widgets and nested layouts from a given layout.
    """
    if layout is None:
        return

    while layout.count():
        # 1. Take the first item from the layout
        item = layout.takeAt(0)
        
        # 2. Check if the item is a Widget
        if item.widget() is not None:
            item.widget().deleteLater()
            
        # 3. Check if the item is a Nested Layout
        elif item.layout() is not None:
            clear_layout(item.layout()) # <--- RECURSION
            
        # 4. (Optional) Handle Spacers (rarely needed, GC handles them)
        # elif item.spacerItem() is not None:
        #    pass