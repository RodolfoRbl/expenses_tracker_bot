import boto3
from boto3.dynamodb.conditions import Key
from datetime import datetime, date, timezone, timedelta
from decimal import Decimal
from typing import List, Dict, Any, Union


class ExpenseDB:
    def __init__(self, region_name: str):
        self.dynamodb = boto3.resource("dynamodb", region_name=region_name)
        self.table_name = "Expenses"
        self.user_states_table = "Telegram_bot_states"
        self.table = self.dynamodb.Table(self.table_name)
        self.state_table = self.dynamodb.Table(self.user_states_table)
        self.region_name = region_name

    def create_table(self) -> None:
        existing_tables = boto3.client("dynamodb", region_name=self.region_name).list_tables()[
            "TableNames"
        ]
        if self.table_name in existing_tables:
            print(f"Table '{self.table_name}' already exists.")
            return

        self.table = self.dynamodb.create_table(
            TableName=self.table_name,
            KeySchema=[
                {"AttributeName": "user_id", "KeyType": "HASH"},
                {"AttributeName": "timestamp", "KeyType": "RANGE"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "user_id", "AttributeType": "S"},
                {"AttributeName": "timestamp", "AttributeType": "S"},
                {"AttributeName": "date", "AttributeType": "S"},
            ],
            GlobalSecondaryIndexes=[
                {
                    "IndexName": "UserDateIndex",
                    "KeySchema": [
                        {"AttributeName": "user_id", "KeyType": "HASH"},
                        {"AttributeName": "date", "KeyType": "RANGE"},
                    ],
                    "Projection": {"ProjectionType": "ALL"},
                    "ProvisionedThroughput": {"ReadCapacityUnits": 1, "WriteCapacityUnits": 1},
                }
            ],
            ProvisionedThroughput={"ReadCapacityUnits": 1, "WriteCapacityUnits": 1},
        )
        self.table.wait_until_exists()
        print(f"Table '{self.table_name}' created.")

    def create_user_state_table(self) -> None:
        existing_tables = boto3.client("dynamodb", region_name=self.region_name).list_tables()[
            "TableNames"
        ]
        if self.user_states_table in existing_tables:
            print(f"Table '{self.user_states_table}' already exists.")
            return

        self.table = self.dynamodb.create_table(
            TableName=self.user_states_table,
            KeySchema=[{"AttributeName": "user_id", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "user_id", "AttributeType": "S"}],
            ProvisionedThroughput={"ReadCapacityUnits": 1, "WriteCapacityUnits": 1},
        )
        self.table.wait_until_exists()
        print(f"Table '{self.user_states_table}' created.")

    def get_state(self, user_id: str) -> Dict[str, Any]:
        """
        Get the state of a user from the user states table.
        """
        response = self.state_table.get_item(Key={"user_id": user_id})
        return response.get("Item", {})

    def _parse_timezone(self, timezone_str: str) -> timezone:
        """
        Parse a timezone string (e.g., 'UTC-6' or 'UTC+3') into a timezone object.
        """
        if timezone_str.startswith("UTC"):
            sign = timezone_str[3]
            offset_hours = int(timezone_str[4:])
            if sign == "-":
                offset = timedelta(hours=-offset_hours)
            elif sign == "+":
                offset = timedelta(hours=offset_hours)
            else:
                raise ValueError("Invalid timezone format. Use 'UTC±X'.")
            return timezone(offset)
        else:
            raise ValueError("Invalid timezone format. Use 'UTC±X'.")

    def insert_expense(
        self,
        user_id: str,
        amount: float,
        category: str,
        currency: str,
        description: str = "",
        income: bool = False,
        timezone: str = "UTC-6",
    ) -> None:

        # Parse the timezone string (e.g., "UTC-6" or "UTC+3")
        tz = self._parse_timezone(timezone)
        current_time = datetime.now(tz)
        timestamp = str(int(current_time.timestamp()))
        date_str = current_time.strftime("%Y-%m-%d")

        item = {
            "user_id": user_id,
            "timestamp": timestamp,
            "date": date_str,
            "amount": Decimal(str(amount)),
            "category": category,
            "currency": currency,
            "description": description,
            "income": income,
        }
        self.table.put_item(Item=item)

    def fetch_expenses_by_user_and_date(
        self, user_id: str, start_date: Union[str, date], end_date: Union[str, date]
    ) -> List[Dict[str, Any]]:
        # Ensure dates are in YYYY-MM-DD format
        if isinstance(start_date, date):
            start_date = start_date.strftime("%Y-%m-%d")
        if isinstance(end_date, date):
            end_date = end_date.strftime("%Y-%m-%d")

        response = self.table.query(
            IndexName="UserDateIndex",
            KeyConditionExpression=Key("user_id").eq(user_id)
            & Key("date").between(start_date, end_date),
        )
        items = response.get("Items", [])

        # Convert date strings back to date objects in the response
        for item in items:
            item["date"] = datetime.strptime(item["date"], "%Y-%m-%d").date()

        return items

    def fetch_latest_expenses(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Fetch the most recent expenses for a user."""
        response = self.table.query(
            KeyConditionExpression=Key("user_id").eq(user_id),
            ScanIndexForward=False,  # Sort in descending order
            Limit=limit,
        )
        return response.get("Items", [])

    def summarize_by_category(self, expenses: List[Dict[str, Any]]) -> Dict[str, float]:
        summary = {}
        for item in expenses:
            category = item.get("category", "uncategorized")
            amount = float(item.get("amount", 0))
            if not item.get("income", False):
                summary[category] = summary.get(category, 0) + amount
            else:
                # Track income separately with a special category
                summary["💰 Income"] = summary.get("💰 Income", 0) + amount
        return summary

    def delete_last_record(self, user_id: str) -> bool:
        latest = self.fetch_latest_expenses(user_id, limit=1)
        if not latest:
            return False
        last_record = latest[0]
        self.table.delete_item(
            Key={"user_id": last_record["user_id"], "timestamp": last_record["timestamp"]}
        )
        return True

    def delete_table(self) -> bool:
        """Delete the DynamoDB table if it exists."""
        try:
            self.table.delete()
            self.table.wait_until_not_exists()
            print(f"Table '{self.table_name}' deleted successfully.")
            return True
        except self.dynamodb.meta.client.exceptions.ResourceNotFoundException:
            print(f"Table '{self.table_name}' does not exist.")
            return False


if __name__ == "__main__":
    db = ExpenseDB(region_name="eu-central-1")

    # Create and populate table
    db.create_table()
    db.create_user_state_table()
    # db.insert_expense(
    #     user_id="123456",
    #     amount=25.5,
    #     category="groceries",
    #     currency="USD",
    #     description="Milk and eggs",
    #     income=False,
    # )

    # # Query data
    # start = date(2024, 1, 1)
    # end = date(2025, 12, 31)
    # records = db.fetch_expenses_by_user_and_date("123456", start, end)
    # print("Fetched records:", records)
    # print("Summary:", db.summarize_by_category(records))

    # Delete table example (uncomment to use)
    # db.delete_table()
