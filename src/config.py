import os
import json
from base.utils import decode_creds

# Dictionary for local testing
if os.getenv("LOCAL_RUN"):
    local_config = json.loads(os.getenv("LOCAL_RUN"))
    TOKEN_GOOGLE = local_config["TOKEN_GOOGLE"]
    TOKEN_BOT = local_config["TOKEN_BOT"]
    MY_CHAT_ID = int(local_config["MY_CHAT_ID"])
    FILE_NAME = local_config["FILE_NAME"]
    SHEET_NAME = local_config["SHEET_NAME"]
else:
    TOKEN_GOOGLE = json.loads(decode_creds(os.getenv("TOKEN_GOOGLE")))
    TOKEN_BOT = os.getenv("TOKEN_BOT")
    MY_CHAT_ID = int(os.getenv("MY_CHAT_ID", 0))
    FILE_NAME = os.getenv("FILE_NAME")
    SHEET_NAME = os.getenv("SHEET_NAME")

commands = {
    "last_records": "Get the last 5 records",
    "delete_last_record": "Delete the last record",
    "debt": "Add debt record",
    "get_debt": "Get the debt records",
    "update_json": "Get the JSON update",
    "find": "Find a pattern in the file",
    "delete_debt": "Delete the last debt record",
    "menu": "Show menu"
}

# Parse modes
HTML = "html"
MARKDOWN = "Markdown"
