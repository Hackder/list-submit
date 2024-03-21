import os

if os.environ.get("MOCK_LIST_SUCCESS") == "1":
    from .mock_list_api import *
elif os.environ.get("MOCK_LIST_FAILURE") == "1":
    from .mock_list_api_failure import *
else:
    from .live_list_api import *
