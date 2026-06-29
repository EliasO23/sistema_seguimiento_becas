import tkinter as tk
from ui.config_view import ConfigView

class AppStub:
    pass

root = tk.Tk()
root.withdraw()
try:
    view = ConfigView(root, AppStub())
    print('ConfigView created')
    for key in ['summary', 'params', 'riesgo', 'sistema']:
        print('Selecting', key)
        view._on_menu_select(key)
        print('Selected', key)
    print('Done')
except Exception as e:
    import traceback
    traceback.print_exc()
finally:
    root.destroy()
