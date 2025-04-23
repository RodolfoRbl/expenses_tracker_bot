from datetime import datetime
from utils.db import ExpenseDB
from utils.general import get_date_with_tz


class RateLimiter:
    def __init__(self, user_id: str, bot_id: str, db: ExpenseDB, max_reqs_allowed=100):
        self.db = db
        self.max_reqs_allowed = max_reqs_allowed
        self.bot_id = str(bot_id)
        self.user_id = str(user_id)
        self.daily_col = "daily_requests"
        self.last_act_col = "last_active"
        self.total_col = "total_requests"
        self.key = {"user_id": self.user_id, "bot_id": self.bot_id}
        self.daily_requests = None
        self.total_requests = None
        self.current_timestamp = str(int(datetime.now().timestamp()))

    def get_current_reqs(self) -> bool:
        """
        Check if user has exceeded their daily rate limit
        """
        today = get_date_with_tz()

        # Get today's requests
        response = self.db.users_table.get_item(
            Key=self.key,
            ProjectionExpression=f"{self.daily_col}, {self.last_act_col}, {self.total_col}",
        ).get("Item", {})
        print("RESPUESTA")
        print(response)
        last_date = response.get(self.last_act_col, "")
        daily_requests = response.get(self.daily_col, 0)
        total_requests = response.get(self.total_col, 0)

        # Reset counter if it's a new day
        last_date_fmt = get_date_with_tz(timestamp=int(last_date)) if last_date else None
        if not last_date_fmt or last_date_fmt != today:
            daily_requests = 0
        self.daily_requests = daily_requests
        self.total_requests = total_requests

    def update_db_reqs(self):
        self.db.users_table.update_item(
            Key=self.key,
            UpdateExpression=f"SET {self.daily_col} = :r, {self.last_act_col} = :d, {self.total_col} = :t",
            ExpressionAttributeValues={
                ":r": int(self.daily_requests + 1),
                ":d": str(self.current_timestamp),
                ":t": int(self.total_requests + 1),
            },
        )

    def get_time_until_reset(self):
        """
        Calculate the time remaining until the daily rate limit resets.
        """
        reset_time = (86400 - (int(self.current_timestamp) % 86400)) // 60
        hours, minutes = divmod(reset_time, 60)
        return f"{hours} hours and {minutes} minutes" if hours else f"{minutes} minutes"

    def is_max_reached(self):
        print(f"Daily: {self.daily_requests}")
        print(f"Total: {self.total_requests}")
        return self.daily_requests >= self.max_reqs_allowed
