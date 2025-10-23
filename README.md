# Expenses Tracker Bot

A Telegram bot that helps you track your daily expenses by storing them in a Google Spreadsheet. Perfect for personal finance management and expense tracking.

## Features

- Record expenses with simple text messages
- View recent expense records
- Search through expense history
- Track debts separately
- Automatic date stamping
- Secure Google Sheets integration

## Prerequisites

- Python 3.9+
- A Telegram account
- Google Cloud Platform account with Sheets API enabled
- AWS account (for Lambda deployment)

## Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/expenses_tracker_bot.git
cd expenses_tracker_bot
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
# Required environment variables
TOKEN_BOT=your_telegram_bot_token
TOKEN_GOOGLE=your_base64_encoded_google_credentials
MY_CHAT_ID=your_telegram_chat_id
FILE_NAME=your_google_sheets_filename
SHEET_NAME=your_sheet_name
EXPENSES_SHORTCUTS=your_sheet_nameyour_dictionary_of_expenses_shortcuts
```

4. Configure Google Sheets:
   - Create a service account in Google Cloud Console
   - Enable Google Sheets API
   - Share your spreadsheet with the service account email
   - Base64 encode your credentials JSON file

## Usage

### Basic Commands

- `/last_records` - Get the last 5 expense records
- `/delete_last_record` - Delete the last record
- `/debt` - Add a debt record
- `/get_debt` - View all debt records
- `/find pattern` - Search for expenses matching pattern
- `/delete_debt` - Delete the last debt record

### Recording Expenses

Simply send a message with amount and description:
```
100 groceries
groceries 100
50.5 taxi ride
```

## Deployment

The bot is designed to run on AWS Lambda. Deployment is automated via GitHub Actions when pushing to the `dev` branch.


## Contributing

1. Fork the repository
2. Create your feature branch: `git checkout -b feature/AmazingFeature`
3. Commit your changes: `git commit -m 'Add some AmazingFeature'`
4. Push to the branch: `git push origin feature/AmazingFeature`
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
