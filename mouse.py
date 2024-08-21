from pynput import mouse

def on_click(x, y, button, pressed):
    if pressed: print(f'({x}, {y})')

def on_scroll(x, y, dx, dy):
    # Stop listener
    return False
    
listener = mouse.Listener(
    on_click=on_click,
    on_scroll=on_scroll)
listener.start()
