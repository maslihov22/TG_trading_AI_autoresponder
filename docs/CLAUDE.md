# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python application that uses the Mistral AI API to analyze Telegram trading conversations. The application acts as an assistant named "X" who analyzes trading dialogue to determine conversation phases (First Deposit vs Redepsit) and generates appropriate Spanish responses. The system includes both a modern GUI interface and console-based tools for comprehensive trading conversation management.

## Development Commands

```bash
# Run the MODERN GUI APPLICATION (RECOMMENDED)
python ui_app.py

# Run the AUTO-RESPONDER (CONSOLE - for automation)
python auto_responder.py

# Run the enhanced script with Telegram integration (CONSOLE - manual analysis)
python main_with_telegram.py

# Run the original script (CONSOLE - static analysis, legacy)
python main.py

# Install dependencies
pip install mistralai telethon flet
```

## Architecture

The application follows a modular design with clear separation of concerns:

- **Configuration Layer** (`config.py`): Centralized configuration for all API credentials and settings
- **Data Access Layer** (`telegram_reader.py`): `TelegramReader` class that handles all Telegram API interactions including connection management, dialog retrieval, message fetching, AI analysis integration, lead detection, real-time monitoring, and read receipt management
- **GUI Layer** (`ui_app.py`): Modern Flet-based graphical interface with real-time updates, visual notifications, dialog management, and integrated auto-responder controls
- **Automation Layer** (`auto_responder.py`): Console-based real-time auto-responder system that monitors for new messages, identifies leads by Spanish language, and automatically responds using AI
- **Application Layer** (`main_with_telegram.py`): Console-based user interface and workflow orchestration that provides three modes: individual dialog analysis, batch analysis, and dialog listing
- **Legacy Script** (`main.py`): Original static analysis script for manual dialog input

### Key Design Patterns

- **Single Responsibility**: Each class/module has one clear purpose
- **Dependency Injection**: AI client and configuration passed to TelegramReader methods
- **Session Management**: Single TelegramReader instance per application run to maintain connection state

## Core Functionality

### TelegramReader Class Methods

**Core Communication:**
- `connect()`: Establishes Telegram session with phone verification
- `get_all_dialogs()`: Retrieves user's dialog list with metadata
- `find_dialog_by_input()`: Smart search by name or UserID
- `get_dialogs_list()`: Formatted dialog listing for UI display
- `send_message()`: Send messages to specific dialogs
- `mark_dialog_as_read()`: Mark dialogs as read in Telegram (sync read receipts)

**Lead Detection & Analysis:**
- `is_spanish_text()`: Determines if text contains Spanish language indicators
- `is_lead_dialog()`: Identifies if a dialog is a lead (Spanish conversation)
- `get_leads_only()`: Retrieve only dialogs with leads (sorted by priority)
- `dialog_needs_response()`: Check if dialog needs response (last message not from us)
- `get_unread_leads()`: Get leads that need responses

**AI Integration:**
- `analyze_dialog_with_ai()` / `analyze_all_dialogs_with_ai()`: Manual AI analysis
- `get_ai_response()`: Get response from AI for given context
- `setup_auto_responder()`: Configure real-time auto-responder with UI callbacks
- `start_monitoring()`: Start real-time message monitoring

**Automation:**
- `process_existing_unread_leads()`: Process existing unread messages on startup

### Dialog Analysis System
- **Trading Phase Detection**: Categorizes conversations into FD (First Deposit) or RD (Redeposit)
- **Stage Identification**: Registration, deposit discussion, objections, payments, completion
- **Spanish Response Generation**: Context-appropriate replies from X persona
- **Structured Output**: Phase, type, context summary, and suggested response

## Setup Requirements

Before using the Telegram integration:

1. **Obtain Telegram API credentials** from https://my.telegram.org/apps
2. **Configure credentials** in `config.py`:
   - `TELEGRAM_API_ID` - Your API ID
   - `TELEGRAM_API_HASH` - Your API Hash
   - `TELEGRAM_PHONE` - Your phone number
3. **Initial authentication** will require SMS verification code

## Application Modes

### Modern GUI Application (`ui_app.py`) - RECOMMENDED INTERFACE
**Modern Flet-based graphical interface with comprehensive features:**

**Key Features:**
- ✅ **Real-time Dialog Management**: Live list of Spanish leads with automatic sorting
- ✅ **Visual Status Indicators**: Blue dots for unread messages (Telegram-style)
- ✅ **Integrated Auto-Responder**: Built-in automation controls with visual feedback
- ✅ **AI Analysis Panel**: Interactive dialog analysis with response editing
- ✅ **Live Statistics**: Real-time counters for leads, processed, and sent messages
- ✅ **Notification System**: Toast notifications for all actions
- ✅ **Read Receipt Sync**: Automatic "read" status synchronization with Telegram
- ✅ **Response Management**: Send, edit, and skip responses with visual feedback

**Interface Layout:**
1. **Status Panel**: Connection status, auto-responder state, and live statistics
2. **Dialog List**: Sorted list of Spanish leads with unread indicators
3. **Analysis Panel**: AI-powered conversation analysis and response suggestions
4. **Control Buttons**: Connect, start auto-responder, refresh dialogs

**Real-time Features:**
- Automatic dialog list updates when new messages arrive
- Visual indicators for dialogs requiring responses
- Live counter updates for all activities
- Instant notification of auto-responder actions
- Telegram-style "blue dot" unread indicators that disappear on click

### Auto-Responder (`auto_responder.py`) - CONSOLE AUTOMATION SYSTEM
**Real-time automation with four modes:**
1. **Production Mode**: Fully automated lead detection and response system
2. **Lead Detection Test**: Test Spanish language detection and lead identification
3. **Unread Detection Test**: Test detection of dialogs needing responses
4. **Exit**: Clean shutdown

**Key Features:**
- ✅ **Automatic Lead Detection**: Identifies Spanish conversations (50%+ Spanish messages)
- ✅ **Real-time Monitoring**: Listens for new incoming messages
- ✅ **Smart Response Logic**: Only responds if last message is not from us
- ✅ **Startup Processing**: Handles existing unread messages on startup
- ✅ **Continuous Operation**: Runs until manually stopped (Ctrl+C)

### Manual Analysis (`main_with_telegram.py`) - CONSOLE INTERFACE
**Interactive console-based analysis with three modes:**
1. **Individual Dialog Analysis**: Search by name or UserID, analyze specific conversation
2. **Batch Processing**: Analyze all user dialogs automatically
3. **Dialog Discovery**: List dialogs with IDs and names for easy identification

### Dialog Search Capabilities
- **Name-based search**: Partial matching, case-insensitive
- **UserID search**: Direct numeric ID lookup
- **Username search**: @username format support

## Automation Workflow

### Auto-Responder Workflow:
1. **Startup**: Connect to Telegram and configure AI client
2. **Initial Scan**: Process existing unread messages from leads
3. **Real-time Monitoring**: Listen for new incoming messages
4. **Lead Detection**: Check if message is from a Spanish conversation
5. **Response Generation**: Generate appropriate response using AI
6. **Message Sending**: Send response and continue monitoring
7. **Continuous Loop**: Repeat until manually stopped

### Lead Identification Logic:
- Analyzes last 10 messages in dialog
- Counts Spanish words and characters (ñ, á, é, í, ó, ú, ¿, ¡)
- Classifies as lead if 50%+ messages contain Spanish
- Only processes private conversations (no groups/channels)

## Session Management

- **Persistent sessions**: `session.session` file stores authentication state
- **Automatic reconnection**: Handles network interruptions gracefully
- **Single instance pattern**: One TelegramReader per application run to avoid API limits
- **Event-driven architecture**: Uses Telethon's event system for real-time monitoring
- **Read receipt synchronization**: Automatic sync of "read" status between GUI and Telegram

## GUI Features (ui_app.py)

### Real-time Interface
- **Live Dialog Updates**: Automatic refresh when new messages arrive
- **Telegram-style Design**: Blue dots for unread, sorted by recency
- **Visual Feedback**: Button animations, progress indicators, status colors
- **Toast Notifications**: Success/error messages with auto-dismiss

### Dialog Management
- **Smart Sorting**: Unread dialogs first, then by timestamp
- **One-click Read**: Click dialog to mark as read (syncs with Telegram)
- **Visual Indicators**: Blue dots for unread, bold text for important dialogs
- **Real-time Counters**: Live statistics for leads, processed, sent

### AI Integration
- **Interactive Analysis**: Click dialog → AI analysis → response suggestions
- **Response Editing**: Built-in editor with save/cancel options
- **Send with Feedback**: Visual button states (sending → success → reset)
- **Skip Tracking**: Count skipped dialogs in statistics

### Auto-Responder Integration
- **GUI Controls**: Start/stop auto-responder from interface
- **Live Status**: Visual indicator of auto-responder state
- **Background Operation**: Auto-responder runs while GUI is active
- **Callback Updates**: GUI updates when auto-responder sends messages

## Security Notes

- API credentials stored in `config.py` should be moved to environment variables for production
- Telegram session files created locally contain authentication tokens
- Mistral API key currently hardcoded in configuration

Always use context7 when I need code generation, setup or configuration steps, or
library/API documentation. This means you should automatically use the Context7 MCP tools to resolve library id and get library docs without me having to explicitly ask. And always respond in russian