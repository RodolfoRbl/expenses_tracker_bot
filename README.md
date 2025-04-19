# Expenses Tracker Bot (Fundu)

A Telegram bot that helps you track your daily expenses with rich analytics and reporting features. Perfect for personal finance management and expense tracking.

## Features

- 💰 Record expenses and income with simple text messages
- 📊 View detailed spending statistics across different time periods
- 📝 Track expenses across multiple categories
- 📆 View expense history with flexible time ranges
- ⚡️ Quick and intuitive expense categorization
- 💎 Premium features available via subscription

## Prerequisites

- Python 3.9+
- A Telegram account
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
# Create a .env file with:
BOT_TOKEN=your_telegram_bot_token
```

## Usage

### Basic Commands

- `/start` - Initialize the bot and see overview
- `/stats` - View spending statistics
- `/list` - See your expense history
- `/delete` - Remove your last record
- `/help` - Show all available commands

### Premium Features

- 👛 Monthly Budget Setting
- 💶 Multi-currency Support
- 📅 Custom Date Recording
- ✏️ Record Editing
- 🫂 Shared Recording
- 🧾 Data Export (Excel/CSV)

### Recording Expenses

Simply send a message with amount and description:
```
100 groceries
50.5 taxi
food 75
```

For income, use the + symbol:
```
+1000 salary
```

### Categories

Available expense categories:
- 🍔 Food
- 🚌 Transport
- 🏠 Rent
- 💡 Utilities
- 🎮 Entertainment
- 🛒 Groceries
- 💊 Health
- 💼 Business
- 🎁 Gifts
- ✈️ Travel
- 📚 Education
- ❓ Other

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