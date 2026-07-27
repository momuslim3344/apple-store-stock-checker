# 🍎 Apple Stock Telegram Bot

Telegram bot to check iPhone 17 256GB availability at Apple Stores in India.

## Features

- 📱 Check stock at all Apple Stores
- 🎨 Check specific color availability
- 🔔 Real-time stock monitoring with alerts
- 👑 Admin panel with user management
- ⏰ Access expiry for users
- 📊 User statistics and tracking

## Commands

### User Commands
- `/start` - Start the bot
- `/help` - Show help
- `/check` - Check all stock
- `/status` - Check bot status
- `/stop` - Stop all monitors

### Admin Commands
- `/admin` - Open admin panel
- `/adduser <user_id> <duration>` - Add user with expiry
- `/removeuser <user_id>` - Remove user
- `/listusers` - List all users
- `/userstats` - Show statistics
- `/openmode` - Allow all users
- `/restrictedmode` - Restrict to authorized users

### Duration Formats
- `1h`, `6h`, `12h` - Hours
- `1d`, `3d`, `7d` - Days
- `15d`, `30d`, `60d` - Days
- `90d`, `180d`, `365d` - Days
- `permanent` - No expiry

## Deploy on Railway

1. Fork this repository
2. Create new project on Railway
3. Add environment variable:
   - `BOT_TOKEN`: Your Telegram bot token
4. Deploy!

## Author

Your Name

## License

MIT