import boto3
from boto3.dynamodb.conditions import Key
from datetime import datetime, date
from decimal import Decimal
from typing import List, Dict, Any, Union
from uuid import uuid4
from utils.dates import parse_timezone, get_str_timestamp


class ExpenseDB:
    def __init__(self, region_name: str):
        self.dynamodb = boto3.resource("dynamodb", region_name=region_name)
        self.table_name = "Expenses"
        self.users_table_name = "Users"
        self.table = self.dynamodb.Table(self.table_name)
        self.users_table = self.dynamodb.Table(self.users_table_name)
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

    def get_fields(
        self, user_id: str, bot_id: str, fields: Union[str, List[str]]
    ) -> Union[Any, Dict[str, Any], None]:
        if isinstance(fields, str):
            fields = [fields]

        projection = ", ".join(fields)

        response = self.users_table.get_item(
            Key={"user_id": str(user_id), "bot_id": str(bot_id)}, ProjectionExpression=projection
        )
        item = response.get("Item", {})

        if len(fields) == 1:
            return item.get(fields[0])
        return item

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
        tz = parse_timezone(timezone)
        current_time = datetime.now(tz)
        uid = str(uuid4())[:7]
        timestamp = str(int(current_time.timestamp()))
        date_str = current_time.strftime("%Y-%m-%d")

        item = {
            "user_id": user_id,
            "timestamp": f"{timestamp}_{uid}",
            "date": date_str,
            "amount": Decimal(str(amount)),
            "category": category,
            "currency": currency,
            "description": description,
            "income": income,
        }
        self.table.put_item(Item=item)

    def fetch_expenses_by_user_and_date(
        self,
        user_id: str,
        start_date: Union[str, date],
        end_date: Union[str, date],
        ascending: bool = True,
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

        # Sort items by timestamp
        items.sort(key=lambda x: x["timestamp"], reverse=not ascending)

        return items

    def fetch_latest_expenses(
        self, user_id: str, limit: int = 50, ascending=False
    ) -> List[Dict[str, Any]]:
        """Fetch the most recent expenses for a user."""
        response = self.table.query(
            KeyConditionExpression=Key("user_id").eq(user_id),
            ScanIndexForward=ascending,  # Sort in descending order
            Limit=limit,
        )
        return list(reversed(response.get("Items", [])))

    def remove_expense(self, user_id: str, timestamp: str) -> bool:
        """
        Remove an expense record by user_id and timestamp.
        """
        try:
            self.table.delete_item(Key={"user_id": user_id, "timestamp": timestamp})
            return True
        except Exception as e:
            print(f"Error deleting item: {e}")
            return False

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

    def remove_batch_records(self, records: dict) -> bool:
        """
        Remove batch records
        """
        items = records
        # Delete each record
        with self.table.batch_writer() as batch:
            for item in items:
                batch.delete_item(Key={"user_id": item["user_id"], "timestamp": item["timestamp"]})

    def insert_batch_records(self, records: list) -> bool:
        """
        Insert batch records
        """
        try:
            with self.table.batch_writer() as batch:
                for item in records:
                    batch.put_item(Item=item)
            return True
        except Exception as e:
            # Log or handle the error properly
            print(f"Error inserting batch records: {e}")
            return False

    def create_users_table(self) -> None:
        client = boto3.client("dynamodb", region_name=self.region_name)

        existing_tables = client.list_tables()["TableNames"]
        if self.users_table_name in existing_tables:
            print(f"Table '{self.users_table_name}' already exists.")
            return

        table = self.dynamodb.create_table(
            TableName=self.users_table_name,
            KeySchema=[
                {"AttributeName": "user_id", "KeyType": "HASH"},
                {"AttributeName": "bot_id", "KeyType": "RANGE"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "user_id", "AttributeType": "S"},
                {"AttributeName": "bot_id", "AttributeType": "S"},
            ],
            ProvisionedThroughput={"ReadCapacityUnits": 1, "WriteCapacityUnits": 1},
        )

        table.wait_until_exists()
        print(f"Table '{self.users_table_name}' created.")

    def add_activity(self, user_id: str, bot_id: str) -> None:
        self.users_table.update_item(
            Key={"user_id": user_id, "bot_id": bot_id},
            UpdateExpression="SET total_requests = if_not_exists(total_requests, :start) + :inc, last_active = :now",
            ExpressionAttributeValues={
                ":inc": 1,
                ":start": 0,
                ":now": get_str_timestamp(),
            },
        )

    def update_field(self, user_id: str, bot_id: str, field: str, value: Any) -> None:
        self.users_table.update_item(
            Key={"user_id": str(user_id), "bot_id": str(bot_id)},
            UpdateExpression="SET #f = :val",
            ExpressionAttributeNames={"#f": field},
            ExpressionAttributeValues={":val": value},
        )


if __name__ == "__main__":
    db = ExpenseDB(region_name="eu-central-1")

    # Create tables
    db.create_table()
    db.create_users_table()
