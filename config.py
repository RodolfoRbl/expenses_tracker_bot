import os
import json

TOKEN_GOOGLE = json.loads(os.getenv("TOKEN_GOOGLE", "{}"))
TOKEN_BOT = os.getenv("TOKEN_BOT")
MY_CHAT_ID = int(os.getenv("MY_CHAT_ID"),)

commands = {
    "last_records": "Get the last 5 records",
    "delete_last_record": "Delete the last record",
    "debt": "Add debt record",
    "get_debt": "Get the debt records",
    "update_json": "Get the JSON update",
    "find": "Find a pattern in the file",
    "delete_debt": "Delete the last debt record",
}

# Parse modes
HTML = "html"
MARKDOWN = "Markdown"
