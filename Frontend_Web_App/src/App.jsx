import { useEffect, useState } from "react";
import "./App.css";

const API = "http://localhost:8000";

function cleanEmailBody(body) {
  if (!body) return "";

  const temp = document.createElement("div");
  temp.innerHTML = body;

  return temp.innerText
    .replace(/\u00a0/g, " ")
    .replace(/\n\s*\n\s*\n/g, "\n\n")
    .trim();
}

function App() {

  const [page, setPage] = useState("loading");

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const [registerMode, setRegisterMode] = useState(false);

  const [currentUser, setCurrentUser] = useState("");

  const [emails, setEmails] = useState([]);

  const [selectedEmail, setSelectedEmail] = useState(null);

  const [analysis, setAnalysis] = useState(null);

  const [analyzing, setAnalyzing] = useState(false);

  const [loadingEmails, setLoadingEmails] = useState(false);

  const [error, setError] = useState("");

  const [success, setSuccess] = useState("");

  const [mailFilter, setMailFilter] = useState("all");

  const [searchTerm, setSearchTerm] = useState("");


// =====================================================
// FILTER EMAILS
// =====================================================

// =====================================================
// FILTER + SEARCH EMAILS
// =====================================================

const filteredEmails = emails.filter((mail) => {

  // SHOW FILTER
  let matchesFilter = true;

  if (mailFilter === "unread") {
    matchesFilter = mail.isUnread === true;
  }

  if (mailFilter === "read") {
    matchesFilter = mail.isUnread !== true;
  }

  // SEARCH
  const search = searchTerm.toLowerCase().trim();

  const matchesSearch =
    search === "" ||
    (mail.subject || "").toLowerCase().includes(search) ||
    (mail.from || "").toLowerCase().includes(search) ||
    (mail.snippet || "").toLowerCase().includes(search) ||
    (mail.body || "").toLowerCase().includes(search);

  // BOTH CONDITIONS MUST MATCH
  return matchesFilter && matchesSearch;
});

// =====================================================
// CHECK LOGIN
// =====================================================

  useEffect(() => {

    checkAppStatus();

  }, []);


  async function checkAppStatus() {

    try {

      const response = await fetch(
        `${API}/app/status`,
        {
          credentials: "include"
        }
      );

      const data = await response.json();

      if (!data.authenticated) {

        setPage("login");

        return;
      }

      setCurrentUser(data.email);

      // Immediately go to loading page
      setPage("loading");

      // Check Gmail in background
      checkGmail();

    } catch (error) {

      console.error(error);

      setPage("login");
    }
  }


  // =====================================================
  // CHECK GMAIL
  // =====================================================

  async function checkGmail() {

    try {

      const response = await fetch(
        `${API}/auth/status`,
        {
          credentials: "include"
        }
      );

      const data = await response.json();

      if (
        response.ok &&
        data.authenticated &&
        data.accounts?.length > 0
      ) {

        loadEmails();

      } else {

        setPage("connect");

      }

    } catch (error) {

      console.error(error);

      setPage("connect");
    }
  }


  // =====================================================
  // LOGIN
  // =====================================================

  async function handleLogin(event) {

    event.preventDefault();

    setError("");
    setSuccess("");

    if (!email || !password) {

      setError(
        "Please enter email and password."
      );

      return;
    }

    try {

      const response = await fetch(
        `${API}/app/login`,
        {
          method: "POST",

          headers: {
            "Content-Type": "application/json"
          },

          credentials: "include",

          body: JSON.stringify({
            email,
            password
          })
        }
      );

      const data = await response.json();

      if (!response.ok) {

        setError(
          data.detail ||
          "Login failed."
        );

        return;
      }

      setCurrentUser(data.email);

      // Immediately leave login page
      setPage("loading");

      // Check Gmail in background
      checkGmail();

    } catch (error) {

      console.error(error);

      setError(
        "Cannot connect to backend."
      );
    }
  }


  // =====================================================
  // REGISTER
  // =====================================================

  async function handleRegister(event) {

    event.preventDefault();

    setError("");
    setSuccess("");

    try {

      const response = await fetch(
        `${API}/app/register`,
        {
          method: "POST",

          headers: {
            "Content-Type": "application/json"
          },

          credentials: "include",

          body: JSON.stringify({
            email,
            password
          })
        }
      );

      const data = await response.json();

      if (!response.ok) {

        setError(
          data.detail ||
          "Registration failed."
        );

        return;
      }

      setSuccess(
        "Account created. Please login."
      );

      setRegisterMode(false);

      setPassword("");

    } catch (error) {

      setError(
        "Cannot connect to backend."
      );
    }
  }


  // =====================================================
  // CONNECT GMAIL
  // =====================================================

  function connectGmail() {

    window.location.href =
      `${API}/login`;
  }


  // =====================================================
  // LOAD EMAILS
  // =====================================================

  async function loadEmails() {

    setLoadingEmails(true);

    setError("");

    try {

      const response = await fetch(
        `${API}/emails?max_results=30`,
        {
          credentials: "include"
        }
      );

      const data = await response.json();

      if (!response.ok) {

        if (response.status === 401) {

          setPage("connect");

          return;
        }

        throw new Error(
          data.detail ||
          "Could not load emails."
        );
      }

      setEmails(
        data.emails || []
      );

      setPage("inbox");

    } catch (error) {

      console.error(error);

      setError(
        error.message ||
        "Could not load emails."
      );

    } finally {

      setLoadingEmails(false);
    }
  }


  // =====================================================
  // OPEN EMAIL INSIDE APP
  // =====================================================

  function selectEmail(mail) {

    setSelectedEmail(mail);

    setAnalysis(null);

    window.scrollTo({
      top: 0,
      behavior: "smooth"
    });
  }


  // =====================================================
  // AI ANALYSIS
  // =====================================================

  async function analyzeEmail() {

    if (!selectedEmail) return;

    setAnalyzing(true);

    setAnalysis(null);

    setError("");

    try {

      const response = await fetch(
        `${API}/analyze-email/${selectedEmail.id}`,
        {
          credentials: "include"
        }
      );

      const data = await response.json();

      if (!response.ok) {

        throw new Error(
          data.detail ||
          "AI analysis failed."
        );
      }

      setAnalysis(data);

    } catch (error) {

      console.error(error);

      setError(
        error.message ||
        "AI analysis failed."
      );

    } finally {

      setAnalyzing(false);
    }
  }


  // =====================================================
  // CLOSE EMAIL
  // =====================================================

  function closeEmail() {

    setSelectedEmail(null);

    setAnalysis(null);
  }


  // =====================================================
  // OPEN ACTUAL GMAIL
  // =====================================================

  function openInGmail() {

    if (!selectedEmail) return;

    window.open(
      `https://mail.google.com/mail/u/0/#inbox/${selectedEmail.id}`,
      "_blank"
    );
  }

// =====================================================
// LOGOUT
// =====================================================

async function logout() {

  try {

    await fetch(
      `${API}/app/logout`,
      {
        method: "POST",
        credentials: "include"
      }
    );

  } catch (error) {

    console.error("Logout error:", error);
  }

  // Clear login fields
  setEmail("");
  setPassword("");

  // Clear current user
  setCurrentUser("");

  // Clear inbox data
  setEmails([]);
  setSelectedEmail(null);

  // Clear AI analysis
  setAnalysis(null);

  // Clear search and filter
  setSearchTerm("");
  setMailFilter("all");

  // Clear messages
  setError("");
  setSuccess("");

  // Reset register mode
  setRegisterMode(false);

  // Navigate to login page
  setPage("login");
}

// =====================================================
  // LOADING
  // =====================================================

  if (page === "loading") {

    return (

      <div className="center-page">

        <div className="loading-box">

          <div className="spinner"></div>

          <h2>
            Loading Smart Inbox...
          </h2>

          <p>
            Checking your account
          </p>

        </div>

      </div>
    );
  }


  // =====================================================
  // LOGIN
  // =====================================================

  if (page === "login") {

    return (
      <div className="auth-page">

        <div className="auth-card">

          <div className="logo">
            📧
          </div>

          <h1>
            Smart Inbox
          </h1>

          <p className="subtitle">
            AI-powered email assistant
          </p>

          <form
            onSubmit={
              registerMode
                ? handleRegister
                : handleLogin
            }
          >

            <input
              type="email"
              placeholder="Email address"
              value={email}
              onChange={
                (e) =>
                  setEmail(e.target.value)
              }
            />

            <input
              type="password"
              placeholder="Password"
              value={password}
              onChange={
                (e) =>
                  setPassword(e.target.value)
              }
            />

            {error && (
              <div className="error-message">
                {error}
              </div>
            )}

            {success && (
              <div className="success-message">
                {success}
              </div>
            )}

            <button
              className="primary-button"
              type="submit"
            >
              {registerMode
                ? "Create Account"
                : "Login"}
            </button>

          </form>

          <button
            className="link-button"
            onClick={() => {

              setRegisterMode(
                !registerMode
              );

              setError("");
              setSuccess("");

            }}
          >

            {registerMode
              ? "Already have an account? Login"
              : "Create a new account"}

          </button>

        </div>

      </div>
    );
  }


  // =====================================================
  // CONNECT GMAIL
  // =====================================================

  if (page === "connect") {

    return (
      <div className="center-page">

        <div className="connect-card">

          <div className="gmail-icon">
            📧
          </div>

          <h1>
            Connect Gmail
          </h1>

          <p>
            Welcome, <strong>{currentUser}</strong>
          </p>

          <p className="muted">
            Connect your Gmail account to view
            your inbox and use AI email analysis.
          </p>

          {error && (
            <div className="error-message">
              {error}
            </div>
          )}

          <button
            className="google-button"
            onClick={connectGmail}
          >
            🔐 Connect Gmail
          </button>

          <button
            className="link-button"
            onClick={logout}
          >
            Logout
          </button>

        </div>

      </div>
    );
  }


  // =====================================================
  // INBOX
  // =====================================================

  return (
    <div className="app-page">

      {/* HEADER */}

      <header className="topbar">

        <div>

          <h1>
            📧 Smart Inbox
          </h1>

          <span>
            {currentUser}
          </span>

        </div>

        <div className="header-actions">

          <button
            onClick={loadEmails}
            className="refresh-button"
          >
            ↻ Refresh
          </button>

          <button
            onClick={logout}
            className="logout-button"
          >
            Logout
          </button>

        </div>

      </header>


      {/* MAIN */}

      <main className="inbox-container">

  <div className="inbox-title">

  <div>
    <h2>Inbox</h2>
    <p>{filteredEmails.length} emails</p>
  </div>

</div>

{/* SEARCH + SHOW FILTER */}

<div className="inbox-controls">

  <div className="mail-search">
    <input
      type="text"
      placeholder="🔍 Search mails..."
      value={searchTerm}
      onChange={(e) => setSearchTerm(e.target.value)}
    />

    {searchTerm && (
      <button
        type="button"
        onClick={() => setSearchTerm("")}
      >
        ✕
      </button>
    )}
  </div>

  <div className="mail-filter">

    <label htmlFor="mailFilter">
      Show:
    </label>

    <select
      id="mailFilter"
      value={mailFilter}
      onChange={(e) =>
        setMailFilter(e.target.value)
      }
    >
      <option value="all">
        All Mails
      </option>

      <option value="unread">
        Unread Mails
      </option>

      <option value="read">
        Read Mails
      </option>
    </select>

  </div>

</div>
        {error && (
          <div className="error-message">
            {error}
          </div>
        )}


        {loadingEmails ? (

          <div className="loading-inbox">

            <div className="spinner"></div>

            <p>
              Loading your emails...
            </p>

          </div>

        ) : (

          <div className="email-list">

            {emails.length === 0 ? (

              <div className="empty-inbox">

                <div>
                  📭
                </div>

                <h3>
                  Your inbox is empty
                </h3>

              </div>

            ) : (

              filteredEmails.map(
                (mail) => (
                  <div
                    key={mail.id}
                    className={
                      `email-row ${
                        mail.isUnread
                          ? "unread"
                          : ""
                      }`
                    }
                    onClick={() =>
                      selectEmail(mail)
                    }
                  >

                    <div className="email-avatar">
                      {(
                        mail.from
                          ?.charAt(0) ||
                        "?"
                      ).toUpperCase()}
                    </div>

                    <div className="email-content">

                      <div className="email-top">

                        <strong>
                          {mail.from ||
                            "Unknown sender"}
                        </strong>

                        <span>
                          {mail.date}
                        </span>

                      </div>

                      <h3>
                        {mail.subject}
                      </h3>

                      <p>
                        {mail.snippet}
                      </p>

                    </div>

                    {mail.isUnread && (
                      <div className="unread-dot">
                      </div>
                    )}

                  </div>

                )
              )

            )}

          </div>

        )}

      </main>


      {/* EMAIL DETAIL */}

      {selectedEmail && (

        <div className="email-overlay">

          <div className="email-modal">

            <div className="modal-header">

              <button
                className="close-button"
                onClick={closeEmail}
              >
                ✕
              </button>

              <h2>
                Email
              </h2>

            </div>


            <div className="email-detail">

              <h1>
                {selectedEmail.subject}
              </h1>

              <div className="email-meta">

                <strong>
                  {selectedEmail.from}
                </strong>

                <span>
                  {selectedEmail.date}
                </span>

              </div>


              <div className="email-body">
                {cleanEmailBody(selectedEmail.body)}
              </div>


              {/* ACTIONS */}

              <div className="email-actions">

                <button
                  className="analyze-button"
                  onClick={analyzeEmail}
                  disabled={analyzing}
                >

                  {analyzing
                    ? "🤖 AI Analyzing..."
                    : "🤖 AI Analyze"}

                </button>

                <button
                  className="open-mail-button"
                  onClick={openInGmail}
                >
                  ↗ Open Mail
                </button>

                <button
                  className="close-analysis-button"
                  onClick={closeEmail}
                >
                  Close
                </button>

              </div>


              {/* AI ANALYSIS */}

              {analysis && (

                <div className="analysis-panel">

                  <div className="analysis-header">

                    <div>

                      <h2>
                        🤖 AI Analysis
                      </h2>

                      <p>
                        Analyzed using Ollama
                      </p>

                    </div>

                    <button
                      className="analysis-close"
                      onClick={() =>
                        setAnalysis(null)
                      }
                    >
                      ✕
                    </button>

                  </div>


                  <div className="analysis-grid">

                    <div className="analysis-card">

                      <span>
                        Category
                      </span>

                      <strong>
                        {analysis.category}
                      </strong>

                    </div>


                    <div className="analysis-card">

                      <span>
                        Priority
                      </span>

                      <strong>
                        {analysis.priority}
                      </strong>

                    </div>

                  </div>


                  <div className="analysis-section">

                    <h3>
                      Summary
                    </h3>

                    <p>
                      {analysis.summary}
                    </p>

                  </div>


                  <div className="analysis-section">

                    <h3>
                      Why?
                    </h3>

                    <p>
                      {analysis.reason}
                    </p>

                  </div>


                  <button
                    className="close-analysis-full"
                    onClick={() =>
                      setAnalysis(null)
                    }
                  >
                    Close Analysis
                  </button>

                </div>

              )}

            </div>

          </div>

        </div>

      )}

    </div>
  );
}


export default App;