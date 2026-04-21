import pygetwindow as gw

def get_active_app_mode():
    try:
        active_window = gw.getActiveWindow()
        if active_window is None:
            return "DEFAULT"
        
        title = active_window.title.lower()
        if "youtube" in title or "browser" in title:
            return "YOUTUBE"
            
        return "DEFAULT"
    except Exception:
        return "DEFAULT"
