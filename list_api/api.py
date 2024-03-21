import os

if os.environ.get("MOCK_LIST") == "1":
    from .mock_list_api import *
else:
    from .live_list_api import *
