<img width="858" height="582" alt="image" src="https://github.com/user-attachments/assets/6de99e3e-b9ef-44ac-b517-58bbbf7200ec" /># Mail AI App

Mail AI App is a full-stack AI-powered email management application designed to connect with Gmail, retrieve and organize emails, and use a locally hosted Large Language Model (LLM) to analyze email content.

The application provides a unified interface for viewing, searching, filtering, analyzing, replying to, and sending emails. Gmail authentication is handled through Google OAuth 2.0, while email analysis and reply generation are performed using Ollama with the Llama 3.2 model.

## Application Preview

<img width="1163" height="701" alt="Mail AI App" src="https://github.com/user-attachments/assets/e80ebe6f-76d5-4ac3-bc6d-2a31b2548ba2" />

## Features

* Smart Inbox for displaying Gmail messages
* Google OAuth 2.0 authentication
* Automatic Gmail account connection
* Email search by subject, sender, snippet, and body
* Read and unread email filtering
* Clean rendering of HTML-based email content
* Removal of unnecessary HTML, CSS, and JavaScript content
* AI-based email categorization
* Email priority detection
* AI-generated email summaries
* AI-generated reasoning for classifications
* AI-assisted reply generation
* Sending emails through Gmail
* Opening selected emails directly in Gmail
* Local AI processing using Ollama

## Technology Stack

### Frontend

* React
* Vite
* JavaScript
* HTML
* CSS

### Backend

* Python
* FastAPI
* Uvicorn
* Pydantic

### Email Services

* Gmail API
* Google OAuth 2.0

### Artificial Intelligence

* Ollama
* Llama 3.2

### Development Tools

* Git
* GitHub
* npm
* Python Virtual Environment

## Repository Structure

```text
mail-ai-app/
│
├── backend/
│   ├── main.py
│   ├── requirements.txt
│   ├── credentials.json
│   ├── .env
│   ├── users.json
│   ├── sessions.json
│   └── tokens/
│
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── App.css
│   │   └── ...
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
│
├── start_app.bat
├── package.json
└── README.md
```

## Prerequisites

The following software is required:

* Python 3.10 or later
* Node.js 18 or later
* npm
* Git
* Ollama
* Google Cloud account with Gmail API enabled

## Installation and Setup

### 1. Clone the Repository

```bash
git clone <your-github-repository-url>
cd mail-ai-app
```

### 2. Backend Setup

Navigate to the backend directory:

```bash
cd backend
```

Create a virtual environment:

```bash
python -m venv venv
```

Activate the virtual environment on Windows:

```bash
.\venv\Scripts\activate
```

For macOS or Linux:

```bash
source venv/bin/activate
```

Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Google Gmail API Configuration

The application uses Google OAuth 2.0 to authenticate users and access Gmail.

Create a project in Google Cloud Console and enable the Gmail API.

Create OAuth 2.0 credentials for a web application and download the credentials file.

Place the file in:

```text
backend/credentials.json
```

The OAuth redirect URI should point to:

```text
http://localhost:8000/auth/callback
```

The Google OAuth configuration must be completed before attempting to connect a Gmail account.

## Environment Configuration

Create a `.env` file inside the `backend` directory.

Example:

```env
FRONTEND_URL=http://localhost:5173
BACKEND_URL=http://localhost:8000
OLLAMA_MODEL=llama3.2
GOOGLE_CREDENTIALS_FILE=credentials.json
```

The frontend and backend URLs should use the same hostname configuration to avoid session and cookie-related issues.

## Ollama Configuration

Install Ollama and verify the installation:

```bash
ollama --version
```

Download the Llama 3.2 model:

```bash
ollama pull llama3.2
```

Verify the model:

```bash
ollama list
```

The application uses the locally running Llama 3.2 model for email analysis and AI-assisted reply generation.

## Running the Backend

From the `backend` directory, run:

```bash
python -m uvicorn main:app --reload
```

The backend will be available at:

```text
http://localhost:8000
```

To verify the backend:

```text
http://localhost:8000/
```

## Running the Frontend

Open a new terminal and navigate to the frontend directory:

```bash
cd frontend
```

Install the dependencies:

```bash
npm install
```

Start the Vite development server:

```bash
npm run dev
```

The frontend will be available at:

```text
http://localhost:5173
```

## Application Workflow

The application follows the workflow below:

```text
User Login
     |
     v
Smart Inbox Authentication
     |
     v
Check Gmail Connection
     |
     +---- Gmail Connected ----+
     |                          |
     |                          v
     |                    Load Inbox
     |
     +---- Gmail Not Connected
                  |
                  v
             Google OAuth
                  |
                  v
          Gmail Authorization
                  |
                  v
             Load Inbox
                  |
                  v
            Select Email
                  |
                  v
        Clean Email Content
                  |
                  v
             AI Analysis
                  |
                  v
       Category / Priority /
       Summary / Reason
```

<img width="1123" height="735" alt="image" src="https://github.com/user-attachments/assets/e6d53b56-7dea-4ca9-9e1a-d0c20b137cfa" />
<img width="1251" height="728" alt="image" src="https://github.com/user-attachments/assets/4a932c16-ac25-44c9-9fd0-d1363ba9dcda" />
<img width="981" height="635" alt="image" src="https://github.com/user-attachments/assets/ec0d8a93-fc43-45bc-88b0-9e22eac7bbf8" />
<img width="858" height="582" alt="image" src="https://github.com/user-attachments/assets/64bcd3b9-8290-4d1c-96f0-4bf3a4a59f4d" />
<img width="852" height="572" alt="image" src="https://github.com/user-attachments/assets/aee0bc5e-2a17-4772-96c0-74376630df1c" />

<img width="1167" height="607" alt="image" src="https://github.com/user-attachments/assets/482af843-b5ac-493c-bc23-e7cb159474e8" />
<img width="1180" height="510" alt="image" src="https://github.com/user-attachments/assets/1bd807dd-d717-4ada-8801-87575035d43a" />
<img width="1226" height="682" alt="image" src="https://github.com/user-attachments/assets/4ec77807-d9cc-4cca-b5c3-166c2c87b6ba" />









## Gmail Integration

After logging into the application, the system checks whether a Gmail account is already connected to the current Smart Inbox session.

If a Gmail account is available, the application automatically retrieves the inbox.

If no Gmail account is connected, the user is redirected to the Google OAuth authorization flow.

The application uses Gmail API scopes required for:

* Reading emails
* Sending emails
* Identifying the authenticated Gmail account

## Email Processing

Gmail messages may contain HTML, CSS, JavaScript, tracking elements, and other formatting information.

The backend processes the email before displaying it to the user.

The processing pipeline removes:

* HTML tags
* CSS style blocks
* JavaScript blocks
* Unnecessary formatting
* Excessive whitespace

Meaningful content such as paragraphs, line breaks, lists, and readable text is preserved.

This allows emails to be displayed as readable messages instead of exposing the underlying HTML structure.

## Email Search and Filtering

The Smart Inbox provides an email search feature.

Search can be performed using:

* Subject
* Sender
* Email snippet
* Email body

The inbox also provides the following filtering options:

```text
All Mails
Unread Mails
Read Mails
```

## AI Email Analysis

When a user selects an email and requests AI analysis, the cleaned email content is provided to the local Ollama model.

The model generates four outputs:

```text
Category
Priority
Summary
Reason
```

The supported categories are:

```text
Placement
Education
Personal
Promotion
Social
Finance
Security
Other
```

Priority is classified as:

```text
High
Medium
Low
```

Example:

```text
Category: Placement
Priority: High
Summary: The email contains information about a new career opportunity.
Reason: The message provides an opportunity that may be relevant to the recipient's career.
```

## AI-Assisted Reply Generation

The application can generate professional email replies using Ollama.

The following information is provided to the AI model:

```text
Sender
Recipient
Subject
Original Email
```

The model generates a concise reply body that can be reviewed before sending.

## Sending Emails

Users can send emails through their connected Gmail account.

The application requires:

```text
Recipient
Subject
Email Body
```

The backend creates the required email message and sends it through the Gmail API.

## Opening Emails in Gmail

Users can open the selected email directly in Gmail from the Smart Inbox interface.

This provides access to the original Gmail interface whenever additional email functionality is required.

## AI Processing Architecture

```text
Gmail
  |
  v
Gmail API
  |
  v
FastAPI Backend
  |
  v
Email Content Extraction
  |
  v
HTML/CSS Cleaning
  |
  v
Clean Email Content
  |
  v
Ollama
  |
  v
Llama 3.2
  |
  v
AI Analysis
  |
  v
React Frontend
  |
  v
Analysis Result
```

## Backend API Endpoints

| Method | Endpoint             | Description                           |
| ------ | -------------------- | ------------------------------------- |
| POST   | `/app/register`      | Register a Smart Inbox account        |
| POST   | `/app/login`         | Authenticate a Smart Inbox user       |
| GET    | `/app/status`        | Check the current application session |
| POST   | `/app/logout`        | End the current application session   |
| GET    | `/login`             | Start Google OAuth authentication     |
| GET    | `/auth/callback`     | Handle the Google OAuth callback      |
| GET    | `/auth/status`       | Check Gmail authentication status     |
| GET    | `/emails`            | Retrieve inbox emails                 |
| GET    | `/emails/{email_id}` | Retrieve an individual email          |
| POST   | `/analyze-email`     | Analyze an email using Ollama         |
| POST   | `/ai/reply`          | Generate an AI-assisted reply         |
| POST   | `/send-email`        | Send an email through Gmail           |

## Security Considerations

The application handles authentication credentials, Gmail OAuth tokens, session information, and email data.

The following files must not be committed to a public repository:

```text
.env
credentials.json
tokens/
sessions.json
users.json
oauth_state.json
```

These files may contain sensitive authentication information or locally stored user data.

## Recommended .gitignore

```gitignore
# Python
venv/
__pycache__/
*.pyc

# Environment
.env

# Google OAuth
credentials.json
tokens/

# Local application data
sessions.json
users.json
oauth_state.json

# Node
node_modules/
dist/

# IDE
.vscode/
.idea/

# Operating system
.DS_Store
Thumbs.db
```

## Challenges and Solutions

### Gmail OAuth Authentication

**Challenge:**
The application requires access to Gmail without requiring users to provide their Gmail password directly to the application.

**Solution:**
Google OAuth 2.0 is used to authorize Gmail access. OAuth credentials are stored locally and associated with the connected Gmail account.

### HTML Email Rendering

**Challenge:**
Many emails contain complex HTML structures, CSS styles, and JavaScript content. Extracting the raw message can result in HTML or CSS being displayed as normal text.

**Solution:**
The backend cleans HTML email content before displaying or analyzing it. CSS and JavaScript blocks are removed while meaningful email content is preserved.

### AI Processing Time

**Challenge:**
Large language models can require several seconds to process an email, particularly when the email contains a large amount of content.

**Solution:**
The application limits the amount of content provided to the AI model and uses controlled output generation to reduce processing time.

### Gmail API Rate Limits

**Challenge:**
Repeated requests for complete Gmail messages can increase API usage and result in Gmail API rate-limit errors.

**Solution:**
The application minimizes unnecessary Gmail API requests and limits the amount of email content processed by the AI system.

### Frontend and Backend Communication

**Challenge:**
The React frontend and FastAPI backend operate on separate local ports, requiring cross-origin communication.

**Solution:**
FastAPI CORS middleware is configured to permit communication between the Vite frontend and FastAPI backend while supporting authenticated session cookies.

## Testing

The following application workflows should be tested:

* User registration
* User login
* User logout
* Gmail OAuth authentication
* Gmail account connection
* Inbox retrieval
* Email selection
* Email content rendering
* Email search
* Read/unread filtering
* AI email analysis
* AI reply generation
* Email sending
* Opening an email in Gmail

## Future Enhancements

Potential improvements include:

* Multi-account Gmail support
* Advanced email classification
* Email analytics
* Attachment analysis
* Calendar integration
* Real-time inbox updates
* AI-based email organization
* Improved Gmail API caching
* Enhanced authentication and security
* More advanced search capabilities

## Project Objective

The objective of Mail AI App is to combine traditional email management with locally hosted artificial intelligence.

The application provides a centralized interface for retrieving, understanding, categorizing, and responding to emails while using Ollama for local AI processing.


