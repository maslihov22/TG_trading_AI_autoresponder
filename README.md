# TG_trading_AI_autoresponder
ИИ-бот для Telegram с автоматическим анализом торговых диалогов с испаноязычными клиентами

# X - AI Telegram Assistant

Advanced AI-powered Telegram bot for automated trading conversation analysis and response. The system operates under the persona of a professional cryptocurrency trader who assists clients with deposits and investments.

## 🚀 Key Features

- **Modern GUI Interface** - Intuitive Flet-based graphical interface with real-time updates
- **AI-Powered Analysis** - Advanced analysis of trading conversations using Mistral AI
- **Lead Detection** - Automatic identification of Spanish-speaking prospects
- **Phase Recognition** - Detection of trading phases (FD/First Deposit vs RD/Redeposit)
- **Real-time Auto-responder** - Monitors and responds to new messages automatically
- **RAG System** - Retrieval-Augmented Generation with knowledge base integration
- **Multi-mode Operation** - GUI, console auto-responder, and manual analysis modes
- **Telegram Integration** - Full integration with Telegram API for seamless messaging

## 📋 System Requirements

- Python 3.8+
- Telegram API credentials (obtained from https://my.telegram.org/apps)
- Mistral AI API key
- Windows/Linux/macOS compatible

## 🛠 Installation

1. **Clone the repository:**
```bash
git clone <repository-url>
cd x-telegram-bot
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Configure credentials:**
Edit `src/config/settings.py`:
- `MISTRAL_API_KEY` - Your Mistral AI API key
- `MISTRAL_MODEL` - Model to use (default: "mistral-small-latest")
- `TELEGRAM_API_ID` - Your Telegram API ID
- `TELEGRAM_API_HASH` - Your Telegram API Hash
- `TELEGRAM_PHONE` - Your phone number with country code

4. **Set up knowledge base:**
The system uses RAG (Retrieval-Augmented Generation) with knowledge base files in the `kb/` directory:
- `banks.jsonl` - Bank information and payment methods
- `fd_behavior.jsonl` - First deposit client behavior
- `rules.jsonl` - Business rules and procedures

## 🎯 Usage Options

### 1. **GUI Application (Recommended)**
Launch the modern graphical interface:
```bash
python src/main.py
```

Features:
- Real-time dialog management with live updates
- Visual status indicators and statistics
- Integrated auto-responder controls
- Interactive dialog analysis panel
- Notification system for all actions
- Read receipt synchronization with Telegram

### 2. **Auto-responder Mode**
Run the automated response system:
```bash
python -c "from src.core.auto_responder import AutoResponder; import asyncio; asyncio.run(AutoResponder().start())"
```

Features:
- Real-time monitoring of new messages
- Automatic lead detection (Spanish conversations)
- AI-generated responses based on knowledge base
- Processing of existing unread messages on startup

### 3. **Manual Analysis Mode**
For individual dialog analysis:
```bash
python src/main.py
```
Then use the console interface to analyze specific dialogs.

## 🏗️ Project Architecture

```
x-telegram-bot/
├── src/                    # Source code
│   ├── main.py            # Main application entry point
│   ├── config/            # Configuration settings
│   │   └── settings.py    # API keys and system settings
│   ├── core/              # Core business logic
│   │   ├── telegram_client.py  # Telegram API integration
│   │   ├── auto_responder.py   # Automated response system
│   │   └── kb_retriever.py     # RAG knowledge base system
│   └── ui/                # Graphical user interface
│       └── app.py         # Flet-based GUI application
├── kb/                    # Knowledge base (RAG system)
│   ├── banks.jsonl        # Banking and payment information
│   ├── fd_behavior.jsonl  # First deposit behavior patterns
│   └── rules.jsonl        # Business rules and procedures
├── docs/                  # Documentation
│   ├── CLAUDE.md          # Developer documentation
│   ├── RAG_SETUP.md       # RAG system setup guide
│   └── EXAMPLE_OUTPUT.md  # Sample AI responses
├── data/                  # Runtime data
├── sessions/              # Telegram session files
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

## 🔧 Core Components

### Telegram Client (`src/core/telegram_client.py`)
- Full Telegram API integration using Telethon
- Dialog and message management
- Spanish language detection
- Lead identification algorithms
- Message sending and read receipt management
- Real-time message monitoring

### Knowledge Base Retriever (`src/core/kb_retriever.py`)
- RAG (Retrieval-Augmented Generation) system
- FAISS vector indexing for fast document retrieval
- Mistral AI embeddings for semantic search
- Dynamic knowledge base updates
- Context-aware response generation

### GUI Application (`src/ui/app.py`)
- Modern Flet-based interface
- Real-time updates and notifications
- Dialog management with visual indicators
- Interactive analysis panels
- Auto-responder controls
- Statistics and monitoring

### Auto-responder (`src/core/auto_responder.py`)
- Real-time message processing
- Intelligent lead detection
- Automated response generation
- Integration with knowledge base
- Continuous operation capabilities

## 🤖 AI Persona: Trading Assistant

The system operates under the persona of a professional cryptocurrency trader who:
- Assists clients with deposit processes (FD - First Deposit)
- Manages redeposit scenarios (RD - Redeposit)
- Provides investment guidance and support
- Responds exclusively in Spanish to Spanish-speaking clients
- Follows predefined business rules and procedures

### Trading Phases:
- **FD (First Deposit)**: Initial contact, deposit discussion, payment processing
- **RD (Redeposit)**: Follow-up deposits, verification processes, commission payments

## 📚 Knowledge Base System (RAG)

The system uses a sophisticated RAG (Retrieval-Augmented Generation) architecture:

### How it Works:
1. **Indexing**: Documents in `kb/` directory are converted to embeddings using Mistral AI
2. **Storage**: Embeddings are indexed in FAISS for fast similarity search
3. **Retrieval**: When processing a message, relevant documents are retrieved based on semantic similarity
4. **Generation**: AI generates responses using both the conversation context and retrieved knowledge

### Document Types:
- **Behavioral patterns**: Client behavior in FD vs RD phases
- **Banking information**: Supported banks and payment methods
- **Business rules**: Commission amounts, procedures, and guidelines
- **Response templates**: Predefined response structures

## 🔐 Security Considerations

- Store API credentials securely (consider environment variables for production)
- Telegram session files contain authentication tokens
- API keys are currently stored in configuration files
- Use secure connections for all external communications

## 🚨 Important Notes

- This system is designed for specific business purposes and follows predetermined scripts
- Misuse of automated messaging systems may violate platform terms of service
- Always comply with local laws and regulations regarding automated messaging
- Monitor system behavior to prevent spam or inappropriate responses

## 🆘 Troubleshooting

### Common Issues:
1. **Telegram Authentication**: If authentication fails, delete the session file in `sessions/` and restart
2. **API Keys**: Verify all API keys are correctly entered in `settings.py`
3. **Dependencies**: Ensure all requirements are installed with `pip install -r requirements.txt`
4. **Knowledge Base**: Verify all `.jsonl` files in `kb/` directory are properly formatted

### Debugging:
- Check console output for error messages
- Verify internet connectivity for API calls
- Ensure Telegram API credentials are valid and authorized

## 📞 Support

For technical support and questions:
- Review documentation in the `docs/` directory
- Check `docs/CLAUDE.md` for detailed developer documentation
- Refer to `docs/RAG_SETUP.md` for knowledge base configuration
- Contact the development team for enterprise support

## 📄 License

This project is intended for educational and demonstration purposes. Use responsibly and in compliance with applicable laws and platform terms of service.
