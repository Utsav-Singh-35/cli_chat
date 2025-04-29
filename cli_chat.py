import os
import re
import time
import argparse
from datetime import datetime
from dotenv import load_dotenv
import google.generativeai as genai
from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel
from rich.table import Table
from rich import box
import requests
from rich.panel import Panel

load_dotenv()

GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
if not GOOGLE_API_KEY:
    raise ValueError("Please set GOOGLE_API_KEY in your .env file")

WEB3FORMS_API_KEY = os.getenv('WEB3FORMS_API_KEY')
if not WEB3FORMS_API_KEY:
    raise ValueError("Please set WEB3FORMS_API_KEY in your .env file")

DEVELOPER_EMAIL = os.getenv('DEVELOPER_EMAIL')
if not DEVELOPER_EMAIL:
    raise ValueError("Please set DEVELOPER_EMAIL in your .env file")

genai.configure(api_key=GOOGLE_API_KEY)

model = genai.GenerativeModel('gemini-2.0-flash')

console = Console()

REVIEW_SCHEMA = {
    "type": "object",
    "properties": {
        "review": {
            "type": "string",
            "description": "User's review of the chat experience"
        },
        "rating": {
            "type": "integer",
            "description": "Rating between 1 and 5",
            "minimum": 1,
            "maximum": 5
        }
    },
    "required": ["review", "rating"]
}

def get_chat_response(prompt):
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error: {str(e)}"

def simulate_typing(text):
    for char in text:
        console.print(char, end="", style="blue")
        time.sleep(0.02)
    console.print()

def analyze_exit_intent(message):
    prompt = f"""
    Analyze if the following message indicates an intent to end a conversation.
    Consider various ways people might express wanting to end a chat, including:
    - Direct statements about leaving/ending
    - Farewells and goodbyes
    - Expressions of completion
    - Indirect hints about wrapping up
    
    Message: "{message}"
    
    Respond with ONLY "yes" if the message indicates an intent to end the conversation,
    or "no" if it does not.
    """
    
    try:
        response = model.generate_content(prompt)
        return response.text.strip().lower() == "yes"
    except Exception as e:
        console.print(f"[red]Error analyzing exit intent: {str(e)}[/red]")
        return False

def is_exit_intent(message):
    return analyze_exit_intent(message)

def collect_feedback():
    console.print("\n[bold yellow]We'd love to hear your feedback![/bold yellow]")
    
    while True:
        review = Prompt.ask("Please share your thoughts about the chat experience")
        if review.strip():
            if len(review) < 10:
                console.print("[red]Please provide more detailed feedback (at least 10 characters)[/red]")
            else:
                break
        else:
            console.print("[red]Feedback cannot be empty. Please share your thoughts.[/red]")
    
    rating_prompt = f"""
    Analyze the following user feedback and determine an appropriate rating from 1 to 5.
    Consider the sentiment, tone, and content of the feedback.
    Respond with ONLY a single number between 1 and 5.
    
    Feedback: "{review}"
    """
    
    try:
        response = model.generate_content(rating_prompt)
        rating = int(response.text.strip())
        rating = max(1, min(5, rating))
        # console.print(f"[green]Based on your feedback, we've assigned a rating of {rating}/5[/green]")
    except Exception as e:
        console.print(f"[red]Error generating rating: {str(e)}[/red]")
        rating = 3 
    
    return {"review": review, "rating": rating}

def send_feedback_email(feedback, session_info):
    try:
        url = "https://api.web3forms.com/submit"
        
        data = {
            "access_key": WEB3FORMS_API_KEY,
            "subject": f"New Chatbot Feedback - Rating: {feedback['rating']}/5",
            "from_name": "Chatbot User",
            "email": "feedback@chatbot.com",
            "message": f"""
            New feedback received from Chatbot session:
            
            Session Details:
            --------------
            Session ID: {session_info['session_id']}
            Start Time: {session_info['start_time']}
            Duration: {session_info['duration']} seconds
            Total Messages: {len(session_info['messages'])//2}
            
            Feedback:
            --------
            Rating: {feedback['rating']}/5
            Review: {feedback['review']}
            
            Chat History:
            ------------
            {chr(10).join(session_info['messages'])}
            """,
            "to": DEVELOPER_EMAIL
        }
        
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        response = requests.post(url, json=data, headers=headers)
        
        if response.status_code == 200:
            console.print("[green]Feedback sent successfully![/green]")
        else:
            console.print(f"[yellow]Error sending feedback: Status code {response.status_code}[/yellow]")
    except Exception as e:
        console.print(f"[red]Error sending feedback: {str(e)}[/red]")

def save_feedback(feedback):
    with open("feedback.txt", "a") as f:
        f.write("\n" + "=" * 50 + "\n")
        f.write("Feedback Entry\n")
        f.write("=" * 50 + "\n")
        f.write(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Rating: {feedback['rating']}/5\n")
        f.write(f"Review: {feedback['review']}\n")
        f.write("=" * 50 + "\n")

def save_chat_history(chat_history):
    with open("chat_history.txt", "a") as f:
        f.write("\n" + "=" * 80 + "\n")
        f.write(f"Session ID: {chat_history['session_id']}\n")
        f.write(f"Start Time: {chat_history['start_time']}\n")
        f.write(f"Duration: {chat_history['duration']} seconds\n")
        f.write(f"Total Messages: {len(chat_history['messages'])//2}\n")
        f.write("-" * 80 + "\n")
        
        for message in chat_history['messages']:
            timestamp = datetime.now().strftime("%H:%M:%S")
            if message.startswith("[User]"):
                f.write(f"[{timestamp}] User: {message[7:]}\n")
            else:
                f.write(f"[{timestamp}] Bot: {message[6:]}\n")
        
        f.write(f"End Time: {chat_history['end_time']}\n")
        f.write("=" * 80 + "\n\n")

def display_session(session):
    console.print("\n" + "=" * 80)
    console.print(Panel.fit(
        "[bold cyan]Session Details[/bold cyan]\n"
        f"Session ID: [yellow]{session['id']}[/yellow]\n"
        f"Start Time: [yellow]{session['start_time']}[/yellow]\n"
        f"Duration: [yellow]{session['duration']}[/yellow] seconds",
        title="Chat Session",
        border_style="cyan"
    ))
    console.print("=" * 80 + "\n")
    
    table = Table(
        show_header=True,
        header_style="bold magenta",
        box=box.ROUNDED,
        title="[bold]Conversation[/bold]",
        title_style="bold cyan",
        width=80,
        padding=(0, 1)
    )
    
    table.add_column("Time", style="dim", width=10)
    table.add_column("Speaker", style="cyan", width=10)
    table.add_column("Message", style="white", width=60)
    
    for message in session["messages"]:
        if message.startswith("[User]"):
            speaker = "User"
            msg = message[7:]
            style = "green"
        else:
            speaker = "Bot"
            msg = message[6:]
            style = "blue"
        
        msg_lines = [msg[i:i+60] for i in range(0, len(msg), 60)]
        for i, line in enumerate(msg_lines):
            if i == 0:
                table.add_row(
                    datetime.now().strftime("%H:%M:%S"),
                    f"[{style}]{speaker}[/{style}]",
                    f"[{style}]{line}[/{style}]"
                )
            else:
                table.add_row(
                    "",
                    "",
                    f"[{style}]{line}[/{style}]"
                )
    
    console.print(table)
    console.print("\n" + "=" * 80 + "\n")

def clear_history():
    if os.path.exists("chat_history.txt"):
        os.remove("chat_history.txt")
        console.print("[green]Chat history cleared successfully![/green]")
    else:
        console.print("[yellow]No chat history found to clear.[/yellow]")

def save_message_to_history(chat_history, message, is_user=True):
    if not os.path.exists("chat_history.txt"):
        with open("chat_history.txt", "w") as f:
            f.write("\n" + "=" * 80 + "\n")
            f.write(f"Session ID: {chat_history['session_id']}\n")
            f.write(f"Start Time: {chat_history['start_time']}\n")
            f.write("-" * 80 + "\n")
    
    with open("chat_history.txt", "a") as f:
        timestamp = datetime.now().strftime("%H:%M:%S")
        if is_user:
            f.write(f"[{timestamp}] User: {message}\n")
        else:
            f.write(f"[{timestamp}] Bot: {message}\n")

def load_chat_history():
    if not os.path.exists("chat_history.txt"):
        return []
    
    sessions = []
    current_session = None
    
    with open("chat_history.txt", "r") as f:
        for line in f:
            line = line.strip()
            if line.startswith("Session ID:"):
                if current_session:
                    sessions.append(current_session)
                current_session = {
                    "id": line.split(": ")[1],
                    "start_time": "",
                    "end_time": "",
                    "duration": "",
                    "messages": []
                }
            elif line.startswith("Start Time:"):
                current_session["start_time"] = line.split(": ")[1]
            elif line.startswith("End Time:"):
                current_session["end_time"] = line.split(": ")[1]
            elif line.startswith("Duration:"):
                current_session["duration"] = line.split(": ")[1]
            elif line.startswith("[") and "]" in line:
                timestamp = line[1:line.index("]")]
                message = line[line.index("]") + 2:].strip()
                current_session["messages"].append(message)
    
    if current_session:
        sessions.append(current_session)
    return sessions

def main():
    parser = argparse.ArgumentParser(description='CLI Chatbot with Gemini AI')
    parser.add_argument('--show-history', action='store_true', help='Show chat history after session')
    parser.add_argument('--list-sessions', action='store_true', help='List all chat sessions')
    parser.add_argument('--view-session', type=str, help='View a specific session by ID')
    parser.add_argument('--clear-history', action='store_true', help='Clear all chat history')
    args = parser.parse_args()

    if args.clear_history:
        clear_history()
        return
    
    if args.list_sessions:
        sessions = load_chat_history()
        if not sessions:
            console.print("[yellow]No chat sessions found.[/yellow]")
            return
        
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Session ID", style="cyan")
        table.add_column("Start Time", style="dim")
        table.add_column("Duration", style="green")
        table.add_column("Messages", style="blue")
        
        for session in sessions:
            table.add_row(
                session["id"],
                session["start_time"],
                session["duration"],
                str(len(session["messages"])//2)
            )
        
        console.print(table)
        return
    
    if args.view_session:
        sessions = load_chat_history()
        session = next((s for s in sessions if s["id"] == args.view_session), None)
        if session:
            display_session(session)
        else:
            console.print(f"[red]Session {args.view_session} not found.[/red]")
        return

    if args.show_history:
        sessions = load_chat_history()
        if sessions:
            display_session(sessions[-1])
        else:
            console.print("[yellow]No chat history found.[/yellow]")
        return

    session_id = datetime.now().strftime("%Y%m%d%H%M%S")
    chat_history = {
        'session_id': session_id,
        'start_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'messages': [],
        'end_time': None,
        'duration': None
    }

    console.print(Panel.fit(
        "[bold green]Welcome to CLI Chatbot![/bold green]\n\n"
        "[bold cyan]Available Commands:[/bold cyan]\n"
        "1. [yellow]Start Chat[/yellow]: Just type your message\n"
        "2. [yellow]Exit Chat[/yellow]: Type any of these:\n"
        "   - bye, exit, end chat, goodbye, quit\n"
        "   - see you, farewell, that's all\n"
        "   - i'm done, stop\n\n"
        "[bold cyan]Command Line Options:[/bold cyan]\n"
        "[yellow]--show-history[/yellow]: View most recent chat session\n"
        "[yellow]--list-sessions[/yellow]: List all chat sessions\n"
        "[yellow]--view-session ID[/yellow]: View specific session\n"
        "[yellow]--clear-history[/yellow]: Clear all chat history\n\n"
        "[bold red]Note:[/bold red] Feedback will be collected when you exit the chat.",
        title="CLI Chatbot",
        border_style="green"
    ))
    
    while True:
        user_input = Prompt.ask("[green]You[/green]")
        chat_history['messages'].append(f"[User] {user_input}")
        save_message_to_history(chat_history, user_input, is_user=True)
        
        if is_exit_intent(user_input):
            chat_history['end_time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            start_time = datetime.strptime(chat_history['start_time'], "%Y-%m-%d %H:%M:%S")
            end_time = datetime.strptime(chat_history['end_time'], "%Y-%m-%d %H:%M:%S")
            chat_history['duration'] = str((end_time - start_time).seconds)
            
            with open("chat_history.txt", "a") as f:
                f.write(f"End Time: {chat_history['end_time']}\n")
                f.write(f"Duration: {chat_history['duration']} seconds\n")
                f.write("=" * 80 + "\n\n")
            
            feedback = collect_feedback()
            save_feedback(feedback)
            
            send_feedback_email(feedback, chat_history)
            
            console.print("\n[bold green]Thank you for chatting! Goodbye! 👋[/bold green]")
            
            if args.show_history:
                display_session(chat_history)
            
            break
            
        response = get_chat_response(user_input)
        chat_history['messages'].append(f"[Bot] {response}")
        save_message_to_history(chat_history, response, is_user=False)
        
        console.print("\n[bold blue]Bot:[/bold blue] ", end="")
        simulate_typing(response)
        console.print()

if __name__ == "__main__":
    main() 