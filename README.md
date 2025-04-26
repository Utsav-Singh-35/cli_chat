# CLI Chatbot

A command-line interface chatbot with interactive chat, session management, and feedback collection.

## Quick Start

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create `.env` file:
```
GOOGLE_API_KEY=your_gemini_api_key
WEB3FORMS_API_KEY=your_web3forms_api_key
DEVELOPER_EMAIL=your_email@example.com
```

3. Run the chatbot:
```bash
python chatbot.py
```

## Key Commands

- Start chat: `python chatbot.py`
- View history: `python chatbot.py --show-history`
- List sessions: `python chatbot.py --list-sessions`
- View session: `python chatbot.py --view-session SESSION_ID`
- Clear history: `python chatbot.py --clear-history`

## Features

- Interactive chat interface
- Session management
- Chat history tracking
- Feedback collection
- Color-coded messages
- Real-time responses

## Exit Commands

Use any of these to end chat:
- "bye", "exit", "end chat"
- "goodbye", "quit", "see you"
- "farewell", "that's all"
- "i'm done", "stop"

## Project Structure

```
cli_chatbot/
├── chatbot.py          # Main implementation
├── requirements.txt    # Dependencies
├── .env               # API keys
├── chat_history.txt   # Chat logs
└── feedback.txt       # Feedback logs
```

## Dependencies

- `google-generativeai`: For Gemini AI integration
- `python-dotenv`: For environment variable management
- `rich`: For CLI formatting and UI
- `requests`: For API calls

## Error Handling

The chatbot includes comprehensive error handling for:
- API connection issues
- Invalid user inputs
- File operation errors
- Feedback validation
- Session management

## Feedback Collection

When a user exits the chat:
1. Rating collection (1-5)
2. Review collection
3. Feedback saving to file
4. Email notification to developer
5. Session details included

## Session Format

Chat sessions are saved in this format:
```
================================================================================
Session ID: [timestamp]
Start Time: [datetime]
--------------------------------------------------------------------------------
[HH:MM:SS] User: [message]
[HH:MM:SS] Bot: [response]
...
End Time: [datetime]
Duration: [seconds]
================================================================================
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Google Gemini AI for the language model
- Web3Forms for the email API
- Rich library for CLI formatting 