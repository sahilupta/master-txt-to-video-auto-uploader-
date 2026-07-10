## Deploy To Heroku

[![Deploy To Heroku](https://www.herokucdn.com/deploy/button.svg)](https://dashboard.heroku.com/new?template=https://github.com/nihubora264/appx-auto-4)

## Code Write ༒☬𝗦AHIL DEVLOPER☬༒


# AppxAutoUploader Telegram Bot

A powerful Telegram bot designed to automatically manage and update class materials from ClassX platform. The bot handles automatic daily updates, file management, and forum organization for educational content.

## 🌟 Features

### Core Functionality
- **Automatic Daily Updates**: Schedule updates at specific times
- **Smart File Management**: Handles videos, PDFs, and YouTube links
- **Forum Organization**: Automatically creates and manages topic-wise content
- **Progress Tracking**: Monitors upload status and prevents duplicates
- **Error Recovery**: Built-in retry mechanism and error handling

### File Support
- 📹 Video files (auto-download and upload)
- 📄 PDF documents
- 🎥 YouTube links (with thumbnails and direct links)

### Scheduling
- ⏰ Custom time-based updates
- 🔄 Daily automatic checks
- 📊 Status notifications
- 💡 Smart duplicate prevention

## 🚀 Setup

### Prerequisites
- Python 3.11 or higher
- MongoDB database
- Telegram Bot Token
- ClassX API access

### Environment Setup

1. Clone the repository:
```bash
git clone https://github.com/yourUSERLINK/AppxAutoUploader.git
cd AppxAutoUploader
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure the bot:
   - Rename `config.example.py` to `config.py`
   - Update the following variables:
     ```python
     BOT_TOKEN = "your_bot_token"
     DB_NAME = "your_db_name"
     API_ID = your_api_id
     API_HASH = "your_api_hash"
     ADMIN_ID = [your_admin_ids]
     DB_URL = "your_mongodb_url"
     LOG_CHANNEL = your_log_channel_id
     ```

### MongoDB Setup

1. Create a MongoDB database
2. Update the `DB_URL` in config.py with your MongoDB connection string
3. Ensure the following collections are created:
   - batch_collection
   - topic_collection
   - msg_id_collection
   - uploaded_files
   - pending_tasks

## 📱 Usage

### Bot Commands

- `/start` - Start the bot
- `/help` - Show help message
- `/legal` - Get Legal Message
- `/id` - Get a Private Chat id
- `/restart` - Use when Bot Stuck


### Adding a New Batch

1. Use `/addbatch` command
2. Follow the prompts to:
   - Enter course ID
   - Select API endpoint
   - Choose target group
   - Set update schedule (HH:MM format)

### Scheduling Updates

1. The bot will automatically:
   - Check for new content at scheduled times
   - Download new files
   - Create topic-wise organization
   - Upload to specified groups
   - Send status updates

### Monitoring

- Updates are logged to the specified LOG_CHANNEL
- Status messages are sent to the user
- Error notifications for any issues
- Progress tracking for downloads/uploads

## 🔧 Advanced Features

### File Processing
- Automatic video format handling
- PDF processing and encryption
- YouTube link processing
- Forum topic organization

### Error Handling
- Automatic retry for failed downloads
- Connection error recovery
- API rate limit handling
- File verification

### Security
- Admin-only access control
- Secure file handling
- API key management
- MongoDB security

## 🛠 Maintenance


### Updating the Bot
1. Pull the latest changes
2. Update dependencies
3. Restart the bot

### Troubleshooting
- Check logs in LOG_CHANNEL
- Verify MongoDB connection
- Ensure proper permissions
- Check API endpoints status

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📞 Support

For support, please join our [༒☬𝗦AHIL DEVLOPER☬༒
]

## ⚠️ Important Notes

- Ensure proper Telegram bot permissions
- Configure correct timezone (IST)
- Maintain stable internet connection
- Monitor disk space for downloads
- Regular database backups recommended
- Hero

---
Made with ❤️ by [༒☬𝗦AHIL DEVLOPER☬༒] 
