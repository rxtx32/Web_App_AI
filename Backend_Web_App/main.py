from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request as GoogleAuthRequest
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

from dotenv import load_dotenv

import ollama
import os
import json
import hashlib
import secrets
import requests
import time
import base64
import re


# =========================================================
# CONFIGURATION
# =========================================================

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CREDENTIALS_FILE = os.getenv(
    "GOOGLE_CREDENTIALS_FILE",
    os.path.join(BASE_DIR, "credentials.json")
)

FRONTEND_URL = os.getenv(
    "FRONTEND_URL",
    "http://localhost:5173"
)

BACKEND_URL = os.getenv(
    "BACKEND_URL",
    "http://127.0.0.1:8000"
)

OLLAMA_MODEL = os.getenv(
    "OLLAMA_MODEL",
    "llama3.2"
)

REDIRECT_URI = f"{BACKEND_URL}/auth/callback"


# =========================================================
# FILES
# =========================================================

TOKENS_DIR = os.path.join(BASE_DIR, "tokens")

USERS_FILE = os.path.join(
    BASE_DIR,
    "users.json"
)

SESSIONS_FILE = os.path.join(
    BASE_DIR,
    "sessions.json"
)

OAUTH_STATE_FILE = os.path.join(
    BASE_DIR,
    "oauth_state.json"
)

os.makedirs(TOKENS_DIR, exist_ok=True)


# =========================================================
# GOOGLE SCOPES
# =========================================================

SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
]


# =========================================================
# FASTAPI
# =========================================================

app = FastAPI(
    title="Smart Inbox AI Assistant"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# MODELS
# =========================================================

class RegisterRequest(BaseModel):
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class AIReplyRequest(BaseModel):
    sender: str
    recipient: str = ""
    subject: str
    body: str


# =========================================================
# SESSION
# =========================================================

SESSION_COOKIE = "smart_inbox_session"

SESSION_DURATION = 60 * 60 * 24 * 7


# =========================================================
# JSON HELPERS
# =========================================================

def load_json_file(path, default):
    if not os.path.exists(path):
        return default

    try:
        with open(path, "r", encoding="utf-8") as file:
            return json.load(file)
    except Exception:
        return default


def save_json_file(path, data):
    with open(path, "w", encoding="utf-8") as file:
        json.dump(
            data,
            file,
            indent=4
        )


# =========================================================
# PASSWORD
# =========================================================

def hash_password(password):
    return hashlib.sha256(
        password.encode("utf-8")
    ).hexdigest()


# =========================================================
# SESSION USER
# =========================================================

def get_session(request: Request):

    session_id = request.cookies.get(
        SESSION_COOKIE
    )

    if not session_id:
        return None

    sessions = load_json_file(
        SESSIONS_FILE,
        {}
    )

    session = sessions.get(session_id)

    if not session:
        return None

    if time.time() > session.get(
        "expires_at",
        0
    ):
        sessions.pop(session_id, None)

        save_json_file(
            SESSIONS_FILE,
            sessions
        )

        return None

    return session


def get_app_user(request: Request):

    session = get_session(request)

    if not session:
        return None

    return session.get("email")


def require_app_user(request: Request):

    email = get_app_user(request)

    if not email:

        raise HTTPException(
            status_code=401,
            detail="Please login to Smart Inbox first."
        )

    return email


# =========================================================
# REGISTER
# =========================================================

@app.post("/app/register")
def register_user(data: RegisterRequest):

    email = data.email.strip().lower()
    password = data.password

    if not email or not password:

        raise HTTPException(
            status_code=400,
            detail="Email and password are required."
        )

    users = load_json_file(
        USERS_FILE,
        {}
    )

    if email in users:

        raise HTTPException(
            status_code=400,
            detail="Account already exists."
        )

    users[email] = {
        "email": email,
        "password": hash_password(password)
    }

    save_json_file(
        USERS_FILE,
        users
    )

    return {
        "success": True,
        "message": "Account created successfully."
    }


# =========================================================
# LOGIN
# =========================================================

@app.post("/app/login")
def login_user(
    data: LoginRequest,
    response: Response
):

    email = data.email.strip().lower()
    password = data.password

    users = load_json_file(
        USERS_FILE,
        {}
    )

    user = users.get(email)

    if not user:

        raise HTTPException(
            status_code=401,
            detail="Invalid email or password."
        )

    if user.get("password") != hash_password(password):

        raise HTTPException(
            status_code=401,
            detail="Invalid email or password."
        )

    session_id = secrets.token_urlsafe(32)

    sessions = load_json_file(
        SESSIONS_FILE,
        {}
    )

    sessions[session_id] = {
        "email": email,
        "gmail_email": None,
        "expires_at": time.time() + SESSION_DURATION
    }

    save_json_file(
        SESSIONS_FILE,
        sessions
    )

    response.set_cookie(
        key=SESSION_COOKIE,
        value=session_id,
        httponly=True,
        samesite="lax",
        secure=False,
        max_age=SESSION_DURATION,
        path="/"
    )

    return {
        "success": True,
        "authenticated": True,
        "email": email
    }


# =========================================================
# APP STATUS
# =========================================================

@app.get("/app/status")
def app_status(request: Request):

    session = get_session(request)

    if not session:

        return {
            "authenticated": False,
            "email": None
        }

    return {
        "authenticated": True,
        "email": session.get("email")
    }


# =========================================================
# APP LOGOUT
# =========================================================

@app.post("/app/logout")
def app_logout(
    request: Request,
    response: Response
):

    session_id = request.cookies.get(
        SESSION_COOKIE
    )

    sessions = load_json_file(
        SESSIONS_FILE,
        {}
    )

    if session_id:

        sessions.pop(
            session_id,
            None
        )

        save_json_file(
            SESSIONS_FILE,
            sessions
        )

    response.delete_cookie(
        key=SESSION_COOKIE,
        path="/"
    )

    return {
        "success": True
    }


# =========================================================
# TOKEN FILE
# =========================================================

def token_file_for_email(email):

    safe_name = hashlib.sha256(
        email.lower().encode("utf-8")
    ).hexdigest()

    return os.path.join(
        TOKENS_DIR,
        f"{safe_name}.json"
    )


# =========================================================
# GOOGLE CREDENTIALS
# =========================================================

def load_user_credentials(email):

    token_file = token_file_for_email(
        email
    )

    if not os.path.exists(token_file):
        return None

    try:

        credentials = Credentials.from_authorized_user_file(
            token_file,
            SCOPES
        )

        if credentials.expired:

            if not credentials.refresh_token:
                return None

            credentials.refresh(
                GoogleAuthRequest()
            )

            with open(
                token_file,
                "w",
                encoding="utf-8"
            ) as file:

                file.write(
                    credentials.to_json()
                )

        return credentials

    except Exception as error:

        print(
            "Credential error:",
            error
        )

        return None


# =========================================================
# GOOGLE EMAIL
# =========================================================

def get_google_email(credentials):

    response = requests.get(
        "https://www.googleapis.com/oauth2/v2/userinfo",
        headers={
            "Authorization":
                f"Bearer {credentials.token}"
        },
        timeout=15
    )

    if response.status_code != 200:

        raise HTTPException(
            status_code=401,
            detail="Could not retrieve Gmail account."
        )

    return response.json().get("email")


# =========================================================
# GMAIL AUTH STATUS
# =========================================================

@app.get("/auth/status")
def auth_status(request: Request):

    app_email = require_app_user(request)

    accounts = []

    for filename in os.listdir(TOKENS_DIR):

        if not filename.endswith(".json"):
            continue

        path = os.path.join(
            TOKENS_DIR,
            filename
        )

        try:

            credentials = Credentials.from_authorized_user_file(
                path,
                SCOPES
            )

            if credentials.expired:

                if not credentials.refresh_token:
                    continue

                credentials.refresh(
                    GoogleAuthRequest()
                )

                with open(
                    path,
                    "w",
                    encoding="utf-8"
                ) as file:

                    file.write(
                        credentials.to_json()
                    )

            email = get_google_email(
                credentials
            )

            if email:
                accounts.append(email)

        except Exception as error:

            print(
                "Auth status error:",
                error
            )

    return {
        "authenticated": len(accounts) > 0,
        "accounts": list(dict.fromkeys(accounts)),
        "app_email": app_email
    }


# =========================================================
# GOOGLE LOGIN
# =========================================================

@app.get("/login")
def google_login(request: Request):

    require_app_user(request)

    if not os.path.exists(
        CREDENTIALS_FILE
    ):

        raise HTTPException(
            status_code=500,
            detail="credentials.json not found."
        )

    flow = Flow.from_client_secrets_file(
        CREDENTIALS_FILE,
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI
    )

    authorization_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
        code_challenge_method="S256"
    )

    save_json_file(
        OAUTH_STATE_FILE,
        {
            "state": state,
            "code_verifier": flow.code_verifier
        }
    )

    return RedirectResponse(
        authorization_url
    )


# =========================================================
# GOOGLE CALLBACK
# =========================================================

@app.get("/auth/callback")
def google_callback(request: Request):

    require_app_user(request)

    code = request.query_params.get(
        "code"
    )

    state = request.query_params.get(
        "state"
    )

    if not code:

        raise HTTPException(
            status_code=400,
            detail="Authorization code missing."
        )

    oauth_data = load_json_file(
        OAUTH_STATE_FILE,
        {}
    )

    saved_state = oauth_data.get(
        "state"
    )

    code_verifier = oauth_data.get(
        "code_verifier"
    )

    if state != saved_state:

        raise HTTPException(
            status_code=400,
            detail="Invalid OAuth state."
        )

    try:

        flow = Flow.from_client_secrets_file(
            CREDENTIALS_FILE,
            scopes=SCOPES,
            redirect_uri=REDIRECT_URI,
            state=state
        )

        flow.code_verifier = code_verifier

        flow.fetch_token(
            code=code
        )

        credentials = flow.credentials

        google_email = get_google_email(
            credentials
        )

        if not google_email:

            raise Exception(
                "Could not determine Gmail address."
            )

        token_file = token_file_for_email(
            google_email
        )

        with open(
            token_file,
            "w",
            encoding="utf-8"
        ) as file:

            file.write(
                credentials.to_json()
            )

        # Store Gmail account in current app session
        session_id = request.cookies.get(
            SESSION_COOKIE
        )

        sessions = load_json_file(
            SESSIONS_FILE,
            {}
        )

        if session_id in sessions:

            sessions[session_id]["gmail_email"] = google_email

            save_json_file(
                SESSIONS_FILE,
                sessions
            )

        save_json_file(
            OAUTH_STATE_FILE,
            {}
        )

        return RedirectResponse(
            f"{FRONTEND_URL}/inbox"
        )

    except Exception as error:

        print(
            "Google OAuth error:",
            error
        )

        raise HTTPException(
            status_code=400,
            detail=f"Google authentication failed: {error}"
        )


# =========================================================
# GET CURRENT GMAIL ACCOUNT
# =========================================================

def get_current_gmail(request: Request):

    session_id = request.cookies.get(
        SESSION_COOKIE
    )

    sessions = load_json_file(
        SESSIONS_FILE,
        {}
    )

    session = sessions.get(
        session_id
    )

    if not session:
        return None

    gmail_email = session.get(
        "gmail_email"
    )

    if gmail_email:
        return gmail_email

    # If session does not contain Gmail yet,
    # automatically use first connected Gmail account.
    for filename in os.listdir(TOKENS_DIR):

        if not filename.endswith(".json"):
            continue

        path = os.path.join(
            TOKENS_DIR,
            filename
        )

        try:

            credentials = Credentials.from_authorized_user_file(
                path,
                SCOPES
            )

            if credentials.expired:

                if not credentials.refresh_token:
                    continue

                credentials.refresh(
                    GoogleAuthRequest()
                )

                with open(
                    path,
                    "w",
                    encoding="utf-8"
                ) as file:

                    file.write(
                        credentials.to_json()
                    )

            email = get_google_email(
                credentials
            )

            if email:

                session["gmail_email"] = email

                sessions[session_id] = session

                save_json_file(
                    SESSIONS_FILE,
                    sessions
                )

                return email

        except Exception:
            continue

    return None


# =========================================================
# GMAIL SERVICE
# =========================================================

def get_gmail_service(request: Request):

    require_app_user(request)

    gmail_email = get_current_gmail(
        request
    )

    if not gmail_email:

        raise HTTPException(
            status_code=401,
            detail="Gmail is not connected."
        )

    credentials = load_user_credentials(
        gmail_email
    )

    if credentials is None:

        raise HTTPException(
            status_code=401,
            detail="Gmail session expired. Please connect Gmail again."
        )

    return build(
        "gmail",
        "v1",
        credentials=credentials
    )


# =========================================================
# EMAIL BODY
# =========================================================

def decode_body(data):

    if not data:
        return ""

    try:

        decoded = base64.urlsafe_b64decode(
            data + "=" * (
                -len(data) % 4
            )
        )

        return decoded.decode(
            "utf-8",
            errors="ignore"
        )

    except Exception:

        return ""


# =========================================================
# EMAIL BODY CLEANING
# =========================================================

def clean_html_email(html):
    if not html:
        return ""

    # Remove style blocks and their CSS
    html = re.sub(
        r"<style\b[^>]*>.*?</style>",
        "",
        html,
        flags=re.IGNORECASE | re.DOTALL
    )

    # Remove script blocks
    html = re.sub(
        r"<script\b[^>]*>.*?</script>",
        "",
        html,
        flags=re.IGNORECASE | re.DOTALL
    )

    # Convert common block-level HTML elements to line breaks
    html = re.sub(
        r"</(p|div|section|article|header|footer|h[1-6]|li|tr)>",
        "\n",
        html,
        flags=re.IGNORECASE
    )

    # Convert <br> to newline
    html = re.sub(
        r"<br\s*/?>",
        "\n",
        html,
        flags=re.IGNORECASE
    )

    # Convert list items to readable lines
    html = re.sub(
        r"<li\b[^>]*>",
        "\n• ",
        html,
        flags=re.IGNORECASE
    )

    # Remove remaining HTML tags
    html = re.sub(
        r"<[^>]+>",
        "",
        html
    )

    # Decode HTML entities
    html = html.replace("&nbsp;", " ")
    html = html.replace("&amp;", "&")
    html = html.replace("&lt;", "<")
    html = html.replace("&gt;", ">")
    html = html.replace("&quot;", '"')
    html = html.replace("&#39;", "'")

    # Remove CSS accidentally appearing as plain text
    html = re.sub(
        r"@media\s*\([^)]*\)\s*\{.*?\}",
        "",
        html,
        flags=re.IGNORECASE | re.DOTALL
    )

    # Clean trailing spaces from every line
    lines = []

    for line in html.splitlines():

        line = line.strip()

        if line:
            lines.append(line)

    # Keep paragraphs separated
    text = "\n\n".join(lines)

    # Prevent excessive blank lines
    text = re.sub(
        r"\n{3,}",
        "\n\n",
        text
    )

    return text.strip()


def extract_email_body(payload):

    if not payload:
        return ""

    plain_text = ""
    html_text = ""

    # -----------------------------------------------------
    # Direct body
    # -----------------------------------------------------

    body_data = payload.get(
        "body",
        {}
    ).get(
        "data"
    )

    if body_data:

        decoded = decode_body(
            body_data
        )

        mime_type = payload.get(
            "mimeType",
            ""
        )

        if mime_type == "text/plain":
            plain_text = decoded

        elif mime_type == "text/html":
            html_text = decoded

        else:
            plain_text = decoded

    # -----------------------------------------------------
    # Multipart body
    # -----------------------------------------------------

    for part in payload.get(
        "parts",
        []
    ):

        mime_type = part.get(
            "mimeType",
            ""
        ).lower()

        # Nested multipart
        if part.get("parts"):

            nested_body = extract_email_body(
                part
            )

            if mime_type == "text/html":

                html_text = nested_body

            elif mime_type == "text/plain":

                plain_text = nested_body

        # Direct part body
        part_data = part.get(
            "body",
            {}
        ).get(
            "data"
        )

        if part_data:

            decoded = decode_body(
                part_data
            )

            if mime_type == "text/plain":

                plain_text = decoded

            elif mime_type == "text/html":

                html_text = decoded

    # -----------------------------------------------------
    # Prefer plain text
    # -----------------------------------------------------

    if plain_text.strip():

        return clean_html_email(
            plain_text
        )

    # -----------------------------------------------------
    # Otherwise clean HTML
    # -----------------------------------------------------

    if html_text.strip():

        return clean_html_email(
            html_text
        )

    return ""
    
# =========================================================
# EMAIL HEADER
# =========================================================

def get_header(headers, name):

    for header in headers:

        if header.get(
            "name",
            ""
        ).lower() == name.lower():

            return header.get(
                "value",
                ""
            )

    return ""


# =========================================================
# GET INBOX
# =========================================================

@app.get("/emails")
def get_emails(
    request: Request,
    max_results: int = 30
):

    service = get_gmail_service(
        request
    )

    try:

        result = service.users().messages().list(
            userId="me",
            maxResults=max_results,
            labelIds=["INBOX"]
        ).execute()

        messages = result.get(
            "messages",
            []
        )

        emails = []

        for item in messages:

            msg = service.users().messages().get(
                userId="me",
                id=item["id"],
                format="full"
            ).execute()

            payload = msg.get(
                "payload",
                {}
            )

            headers = payload.get(
                "headers",
                []
            )

            subject = get_header(
                headers,
                "Subject"
            )

            sender = get_header(
                headers,
                "From"
            )

            recipient = get_header(
                headers,
                "To"
            )

            date = get_header(
                headers,
                "Date"
            )

            body = extract_email_body(
                payload
            )

            emails.append({

                "id": msg.get(
                    "id"
                ),

                "threadId": msg.get(
                    "threadId"
                ),

                "subject": subject or "(No Subject)",

                "from": sender,

                "to": recipient,

                "date": date,

                "body": body,

                "snippet": msg.get(
                    "snippet",
                    ""
                ),

                "isUnread": "UNREAD" in msg.get(
                    "labelIds",
                    []
                ),

                "labelIds": msg.get(
                    "labelIds",
                    []
                )

            })

        return {
            "emails": emails
        }

    except Exception as error:

        print(
            "Inbox error:",
            error
        )

        raise HTTPException(
            status_code=500,
            detail=f"Could not load emails: {error}"
        )


# =========================================================
# GET SINGLE EMAIL
# =========================================================

@app.get("/emails/{email_id}")
def get_single_email(
    email_id: str,
    request: Request
):

    service = get_gmail_service(
        request
    )

    try:

        msg = service.users().messages().get(
            userId="me",
            id=email_id,
            format="full"
        ).execute()

        payload = msg.get(
            "payload",
            {}
        )

        headers = payload.get(
            "headers",
            []
        )

        return {

            "id": msg.get(
                "id"
            ),

            "threadId": msg.get(
                "threadId"
            ),

            "subject": get_header(
                headers,
                "Subject"
            ) or "(No Subject)",

            "from": get_header(
                headers,
                "From"
            ),

            "to": get_header(
                headers,
                "To"
            ),

            "date": get_header(
                headers,
                "Date"
            ),

            "body": extract_email_body(
                payload
            ),

            "snippet": msg.get(
                "snippet",
                ""
            ),

            "isUnread": "UNREAD" in msg.get(
                "labelIds",
                []
            )

        }

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=f"Could not load email: {error}"
        )


# AI ANALYSIS
@app.get("/analyze-email/{email_id}")
def analyze_email(email_id: str, request: Request):

    service = get_gmail_service(request)

    try:
        msg = service.users().messages().get(
            userId="me",
            id=email_id,
            format="full"
        ).execute()

        payload = msg.get("payload", {})
        headers = payload.get("headers", [])

        subject = get_header(headers, "Subject") or "(No Subject)"
        sender = get_header(headers, "From")

        body = extract_email_body(payload)

                # Clean HTML email content
        body = body or ""

        # Remove CSS/style blocks completely
        body = re.sub(
            r"<style\b[^>]*>.*?</style>",
            " ",
            body,
            flags=re.IGNORECASE | re.DOTALL
        )

        # Remove JavaScript blocks completely
        body = re.sub(
            r"<script\b[^>]*>.*?</script>",
            " ",
            body,
            flags=re.IGNORECASE | re.DOTALL
        )

        # Remove HTML tags
        body = re.sub(
            r"<[^>]+>",
            " ",
            body
        )

        # Remove CSS that appears as plain text
        body = re.sub(
            r"@media\s*\([^)]*\)\s*\{.*?\}",
            " ",
            body,
            flags=re.IGNORECASE | re.DOTALL
        )

        # Decode common HTML entities
        body = body.replace("&nbsp;", " ")
        body = body.replace("&amp;", "&")
        body = body.replace("&lt;", "<")
        body = body.replace("&gt;", ">")
        body = body.replace("&quot;", '"')
        body = body.replace("&#39;", "'")

        # Clean spaces
        body = re.sub(r"[ \t]+", " ", body)
        body = re.sub(r"\n\s*\n\s*\n+", "\n\n", body)

        body = body.strip()

        # Send only 3000 characters to Ollama
        body = body[:3000]

        prompt = f"""Analyze this email.

Subject: {subject}
From: {sender}

Email:
{body}

Return exactly:

Category: <one category>
Priority: <High, Medium, or Low>
Summary: <one short sentence>
Reason: <one short sentence>

Category must be exactly one of:
Placement
Education
Personal
Promotion
Social
Finance
Security
Other
"""

        result = ollama.chat(
            model=OLLAMA_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            options={
                "temperature": 0,
                "num_predict": 100
            }
        )

        analysis = result["message"]["content"].strip()

        category = "Other"
        priority = "Medium"
        summary = ""
        reason = ""

        for line in analysis.splitlines():

            line = line.strip()

            if line.lower().startswith("category:"):
                category = line.split(":", 1)[1].strip()

            elif line.lower().startswith("priority:"):
                priority = line.split(":", 1)[1].strip()

            elif line.lower().startswith("summary:"):
                summary = line.split(":", 1)[1].strip()

            elif line.lower().startswith("reason:"):
                reason = line.split(":", 1)[1].strip()

        return {
            "success": True,
            "category": category,
            "priority": priority,
            "summary": summary,
            "reason": reason,
            "analysis": analysis
        }

    except Exception as error:

        print("AI analysis error:", error)

        raise HTTPException(
            status_code=500,
            detail=f"AI analysis failed: {error}"
        )

# =========================================================
# AI REPLY
# =========================================================

@app.post("/ai/reply")
@app.post("/ai/reply/")
def ai_reply(
    data: AIReplyRequest,
    request: Request
):

    get_gmail_service(
        request
    )

    prompt = f"""
You are a professional email assistant.

Write a concise and professional reply.

Sender:
{data.sender}

Recipient:
{data.recipient}

Subject:
{data.subject}

Original email:
{data.body}

Return only the reply body.
Do not include a subject line.
"""

    try:

        result = ollama.chat(
            model=OLLAMA_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        reply = result[
            "message"
        ][
            "content"
        ].strip()

        return {
            "success": True,
            "reply": reply
        }

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=f"AI reply generation failed: {error}"
        )


# =========================================================
# SEND EMAIL
# =========================================================

@app.post("/send-email")
def send_email(
    data: dict,
    request: Request
):

    service = get_gmail_service(
        request
    )

    to = str(
        data.get(
            "to",
            ""
        )
    ).strip()

    subject = str(
        data.get(
            "subject",
            ""
        )
    ).strip()

    body = str(
        data.get(
            "body",
            ""
        )
    ).strip()

    if not to:

        raise HTTPException(
            status_code=400,
            detail="Recipient email is required."
        )

    if not subject:

        raise HTTPException(
            status_code=400,
            detail="Subject is required."
        )

    if not body:

        raise HTTPException(
            status_code=400,
            detail="Email body is required."
        )

    try:

        from email.mime.text import MIMEText

        message = MIMEText(
            body,
            "plain",
            "utf-8"
        )

        message["to"] = to
        message["subject"] = subject

        raw = base64.urlsafe_b64encode(
            message.as_bytes()
        ).decode()

        sent = service.users().messages().send(
            userId="me",
            body={
                "raw": raw
            }
        ).execute()

        return {

            "success": True,

            "message": "Email sent successfully.",

            "id": sent.get(
                "id"
            )

        }

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=f"Could not send email: {error}"
        )


# =========================================================
# ROOT
# =========================================================

@app.get("/")
def root():

    return {
        "message":
            "Smart Inbox AI Backend is running successfully."
    }