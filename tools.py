import logging
from livekit.agents import function_tool, RunContext
import requests
from langchain_community.tools import DuckDuckGoSearchRun
import os
import smtplib
from email.mime.multipart import MIMEMultipart  
from email.mime.text import MIMEText
from typing import Optional, Literal


@function_tool()
async def get_weather(
    context: RunContext,  # type: ignore
    city: str) -> str:
    """
    Get the current weather for a given city.
    """
    try:
        response = requests.get(
            f"https://wttr.in/{city}?format=3")
        if response.status_code == 200:
            logging.info(f"Weather for {city}: {response.text.strip()}")
            return response.text.strip()   
        else:
            logging.error(f"Failed to get weather for {city}: {response.status_code}")
            return f"Could not retrieve weather for {city}."
    except Exception as e:
        logging.error(f"Error retrieving weather for {city}: {e}")
        return f"An error occurred while retrieving weather for {city}." 

@function_tool()
async def search_web(
    context: RunContext,  # type: ignore
    query: str) -> str:
    """
    Search the web using DuckDuckGo.
    """
    try:
        results = DuckDuckGoSearchRun().run(tool_input=query)
        logging.info(f"Search results for '{query}': {results}")
        return results
    except Exception as e:
        logging.error(f"Error searching the web for '{query}': {e}")
        return f"An error occurred while searching the web for '{query}'."    

@function_tool()    
async def send_email(
    context: RunContext,  # type: ignore
    to_email: str,
    subject: str,
    message: str,
    cc_email: Optional[str] = None
) -> str:
    """
    Send an email through Gmail.
    
    Args:
        to_email: Recipient email address
        subject: Email subject line
        message: Email body content
        cc_email: Optional CC email address
    """
    try:
        # Gmail SMTP configuration
        smtp_server = "smtp.gmail.com"
        smtp_port = 587
        
        # Get credentials from environment variables
        gmail_user = os.getenv("GMAIL_USER")
        gmail_password = os.getenv("GMAIL_PASS")  # Use App Password, not regular password
        
        if not gmail_user or not gmail_password:
            logging.error("Gmail credentials not found in environment variables")
            return "Email sending failed: Gmail credentials not configured."
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = gmail_user
        msg['To'] = to_email
        msg['Subject'] = subject
        
        # Add CC if provided
        recipients = [to_email]
        if cc_email:
            msg['Cc'] = cc_email
            recipients.append(cc_email)
        
        # Attach message body
        msg.attach(MIMEText(message, 'plain'))
        
        # Connect to Gmail SMTP server
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()  # Enable TLS encryption
        server.login(gmail_user, gmail_password)
        
        # Send email
        text = msg.as_string()
        server.sendmail(gmail_user, recipients, text)
        server.quit()
        
        logging.info(f"Email sent successfully to {to_email}")
        return f"Email sent successfully to {to_email}"
        
    except smtplib.SMTPAuthenticationError:
        logging.error("Gmail authentication failed")
        return "Email sending failed: Authentication error. Please check your Gmail credentials."
    except smtplib.SMTPException as e:
        logging.error(f"SMTP error occurred: {e}")
        return f"Email sending failed: SMTP error - {str(e)}"
    except Exception as e:
        logging.error(f"Error sending email: {e}")
        return f"An error occurred while sending email: {str(e)}"


@function_tool()
async def manage_notes(
    context: RunContext,  # type: ignore
    action: Literal["add", "remove", "list", "clear"],
    note: Optional[str] = None
) -> str:
    """
    Manage a simple in-memory to-do/notes list.

    Args:
        action: Action to perform - "add", "remove", "list", or "clear".
        note: Note text (required for 'add' and 'remove').

    Returns:
        Result message.
    """
    try:
        if action == "add":
            if not note:
                return "Please specify a note to add."
            notes_memory.append(note)
            logging.info(f"Note added: {note}")
            return f"✅ Note added: '{note}'"

        elif action == "remove":
            if not note:
                return "Please specify a note to remove."
            if note in notes_memory:
                notes_memory.remove(note)
                logging.info(f"Note removed: {note}")
                return f"🗑️ Note removed: '{note}'"
            else:
                return f"⚠️ Note not found: '{note}'"

        elif action == "list":
            if not notes_memory:
                return "📝 Your to-do list is empty."
            formatted = "\n".join(f"{i+1}. {n}" for i, n in enumerate(notes_memory))
            return f"📋 Your notes:\n{formatted}"

        elif action == "clear":
            notes_memory.clear()
            logging.info("All notes cleared.")
            return "🧹 All notes cleared."

        else:
            return "⚠️ Invalid action. Use 'add', 'remove', 'list', or 'clear'."

    except Exception as e:
        logging.error(f"Error in manage_notes: {e}")
        return f"❌ Error managing notes: {str(e)}"
    


todo_list = []

@function_tool()
async def manage_todo(
    context: RunContext,  # type: ignore
    action: Literal["add", "remove", "list", "complete", "clear"],
    task: Optional[str] = None
) -> str:
    """
    Manage a simple in-memory to-do list with task status.

    Args:
        action: The action to perform - "add", "remove", "list", "complete", or "clear".
        task: The task description (required for 'add', 'remove', and 'complete').

    Returns:
        A status message.
    """
    try:
        if action == "add":
            if not task:
                return "Please specify a task to add."
            todo_list.append({"task": task, "done": False})
            logging.info(f"Task added: {task}")
            return f"✅ Task added: '{task}'"

        elif action == "remove":
            if not task:
                return "Please specify a task to remove."
            for t in todo_list:
                if t["task"] == task:
                    todo_list.remove(t)
                    logging.info(f"Task removed: {task}")
                    return f"🗑️ Task removed: '{task}'"
            return f"⚠️ Task not found: '{task}'"

        elif action == "complete":
            if not task:
                return "Please specify a task to mark as completed."
            for t in todo_list:
                if t["task"] == task:
                    t["done"] = True
                    logging.info(f"Task marked as complete: {task}")
                    return f"✅ Task completed: '{task}'"
            return f"⚠️ Task not found: '{task}'"

        elif action == "list":
            if not todo_list:
                return "📝 Your to-do list is empty."
            formatted = "\n".join(
                f"{i + 1}. [{'✔️' if t['done'] else '❌'}] {t['task']}"
                for i, t in enumerate(todo_list)
            )
            return f"📋 Your To-Do List:\n{formatted}"

        elif action == "clear":
            todo_list.clear()
            logging.info("To-do list cleared.")
            return "🧹 All tasks cleared."

        else:
            return "⚠️ Invalid action. Use 'add', 'remove', 'list', 'complete', or 'clear'."

    except Exception as e:
        logging.error(f"Error in manage_todo: {e}")
        return f"❌ Error managing to-do list: {str(e)}"
    



@function_tool()
async def create_tool(
    context: RunContext,  # type: ignore
    function_name: str,
    purpose: str,
    api_url: Optional[str] = None,
    api_host: Optional[str] = None,
    api_key_env: Optional[str] = "RAPIDAPI_KEY"
) -> str:
    """
    Dynamically creates a new function in tools.py and registers it in agent.py.

    Args:
        function_name: Name of the function.
        purpose: Description of what the function should do.
        api_url: Optional API URL to call.
        api_host: Optional RapidAPI host (for headers).
        api_key_env: The environment variable name where API key is stored.
    """
    try:
        tools_file = "tools.py"
        agent_file = "agent.py"

        # Function template
        function_code = f"""
@function_tool()
async def {function_name}(context: RunContext, query: str) -> str:
    \"\"\"
    {purpose}
    \"\"\"
    import requests
    url = "{api_url or 'https://example.com/api'}"
    headers = {{
        "X-RapidAPI-Key": os.getenv("{api_key_env}"),
        "X-RapidAPI-Host": "{api_host or api_url.split('/')[2]}"
    }}
    try:
        response = requests.get(url, headers=headers)
        data = response.json()
        return str(data)
    except Exception as e:
        return f"❌ Error fetching data: {{e}}"
"""

        # Step 1: Append function to tools.py
        with open(tools_file, "a") as f:
            f.write(function_code + "\n")

        # Step 2: Modify agent.py
        with open(agent_file, "r") as f:
            agent_code = f.read()

        # Insert import
        if f"from tools import {function_name}" not in agent_code:
            agent_code = agent_code.replace(
                "from tools import",
                f"from tools import {function_name},"
            )

        # Insert in tools list
        if function_name not in agent_code:
            agent_code = agent_code.replace(
                "tools=[",
                f"tools=[\n                {function_name},"
            )

        with open(agent_file, "w") as f:
            f.write(agent_code)

        return f"✅ Function `{function_name}` created and registered successfully."

    except Exception as e:
        return f"❌ Failed to create function: {str(e)}"
