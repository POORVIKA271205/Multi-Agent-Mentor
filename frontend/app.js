/* Multi Agent Mentor  — single-file vanilla JS SPA (no build step required) */

const API_BASE = "http://127.0.0.1:5000/api";

const state = {
  token: localStorage.getItem("cp_token") || null,
  user: JSON.parse(localStorage.getItem("cp_user") || "null"),
  page: "dashboard",
  authMode: "login", // or 'register'
  loading: false,
  // page-local caches
  dashboard: null,
  questions: null,
  answers: {},
  assessmentResults: null,
  roadmapCareers: [],
  roadmap: null,
  resumeResult: null,
  jobCareers: [],
  jobResults: null,
  jobSkillsInput: "",
  chatLog: [],
};

const NAV_ITEMS = [
  { id: "dashboard", label: "Dashboard", icon: "🏠" },
  { id: "assessment", label: "Career Assessment", icon: "🧭" },
  { id: "roadmap", label: "Learning Roadmap", icon: "🗺️" },
  { id: "resume", label: "Resume Review", icon: "📄" },
  { id: "chat", label: "Career Chat", icon: "💬" },
  { id: "jobs", label: "Job Recommendation", icon: "💼" },
  { id: "profile", label: "Profile", icon: "👤" },
];

// ---------------------------------------------------------------------------
// API helper
// ---------------------------------------------------------------------------

async function api(path, { method = "GET", body, auth = true } = {}) {
  const headers = { "Content-Type": "application/json" };
  if (auth && state.token) headers["Authorization"] = `Bearer ${state.token}`;
  let res;
  try {
    res = await fetch(`${API_BASE}${path}`, {
      method,
      headers,
      body: body ? JSON.stringify(body) : undefined,
    });
  } catch (err) {
    throw new Error("Cannot reach backend. Make sure the Flask server is running at http://127.0.0.1:5000");
  }
  let data = {};
  try { data = await res.json(); } catch (e) { /* no body */ }
  if (!res.ok) {
    if (res.status === 401) {
      logout();
      throw new Error(data.error || "Session expired. Please log in again.");
    }
    throw new Error(data.error || "Something went wrong");
  }
  return data;
}

function showToast(message, type = "success") {
  const existing = document.querySelector(".toast");
  if (existing) existing.remove();
  const el = document.createElement("div");
  el.className = `toast ${type}`;
  el.textContent = message;
  document.body.appendChild(el);
  setTimeout(() => el.remove(), 3500);
}

// ---------------------------------------------------------------------------
// Auth
// ---------------------------------------------------------------------------

function setSession(token, user) {
  state.token = token;
  state.user = user;
  localStorage.setItem("cp_token", token);
  localStorage.setItem("cp_user", JSON.stringify(user));
}

function logout() {
  state.token = null;
  state.user = null;
  localStorage.removeItem("cp_token");
  localStorage.removeItem("cp_user");
  state.page = "dashboard";
  render();
}

async function handleAuthSubmit(e) {
  e.preventDefault();
  const errBox = document.getElementById("auth-error");
  errBox.style.display = "none";
  const submitBtn = document.getElementById("auth-submit-btn");
  submitBtn.disabled = true;
  submitBtn.innerHTML = `<span class="spinner"></span>`;

  try {
    if (state.authMode === "login") {
      const email = document.getElementById("login-email").value.trim();
      const password = document.getElementById("login-password").value;
      const data = await api("/auth/login", { method: "POST", body: { email, password }, auth: false });
      setSession(data.token, data.user);
    } else {
      const name = document.getElementById("reg-name").value.trim();
      const email = document.getElementById("reg-email").value.trim();
      const password = document.getElementById("reg-password").value;
      const data = await api("/auth/register", { method: "POST", body: { name, email, password }, auth: false });
      setSession(data.token, data.user);
    }
    state.page = "dashboard";
    render();
  } catch (err) {
    errBox.textContent = err.message;
    errBox.style.display = "block";
    submitBtn.disabled = false;
    submitBtn.textContent = state.authMode === "login" ? "Log In" : "Create Account";
  }
}

function toggleAuthMode() {
  state.authMode = state.authMode === "login" ? "register" : "login";
  render();
}

// ---------------------------------------------------------------------------
// Navigation
// ---------------------------------------------------------------------------

function goTo(page) {
  state.page = page;
  render();
  loadPageData(page);
}

async function loadPageData(page) {
  try {
    if (page === "dashboard") {
      state.dashboard = await api("/dashboard");
      render();
    } else if (page === "assessment" && !state.questions) {
      const data = await api("/assessment/questions", { auth: false });
      state.questions = data.questions;
      render();
    } else if (page === "roadmap") {
      const [careersData, currentData] = await Promise.all([
        api("/roadmap/careers", { auth: false }),
        api("/roadmap/current"),
      ]);
      state.roadmapCareers = careersData.careers;
      state.roadmap = currentData.roadmap;
      render();
    } else if (page === "jobs" && state.jobCareers.length === 0) {
      const data = await api("/jobs/careers", { auth: false });
      state.jobCareers = data.careers;
      render();
    } else if (page === "chat" && state.chatLog.length === 0) {
      const data = await api("/chat/history");
      state.chatLog = data.history;
      render();
    }
  } catch (err) {
    showToast(err.message, "error");
  }
}

// ---------------------------------------------------------------------------
// Dashboard page
// ---------------------------------------------------------------------------

function renderDashboard() {
  const d = state.dashboard;
  if (!d) {
    return `<div class="page-header"><h1>Dashboard</h1></div><div class="card"><span class="spinner"></span> Loading...</div>`;
  }
  const top = d.top_career;
  const rp = d.roadmap_progress;

  return `
    <div class="page-header">
      <h1>Welcome back, ${escapeHtml(d.user_name)} 👋</h1>
      <p>Here's a snapshot of your career journey so far.</p>
    </div>
    <div class="grid grid-4" style="margin-bottom:18px;">
      <div class="card stat-card">
        <div class="label">Assessments Taken</div>
        <div class="value">${d.assessments_count}</div>
        <div class="sub">Career Assessment Agent</div>
      </div>
      <div class="card stat-card">
        <div class="label">Resume Score</div>
        <div class="value">${d.resume_score !== null ? d.resume_score + "/100" : "—"}</div>
        <div class="sub">Resume Review Agent</div>
      </div>
      <div class="card stat-card">
        <div class="label">Roadmap Progress</div>
        <div class="value">${rp ? rp.percent + "%" : "—"}</div>
        <div class="sub">${rp ? rp.career : "No roadmap yet"}</div>
      </div>
      <div class="card stat-card">
        <div class="label">Chat Messages</div>
        <div class="value">${d.chats_count}</div>
        <div class="sub">Career Chat Agent</div>
      </div>
    </div>
    <div class="grid grid-2">
      <div class="card">
        <h3 style="margin-bottom:14px;">🎯 Top Career Match</h3>
        ${top ? `
          <div style="font-size:20px;font-family:var(--font-heading);font-weight:700;margin-bottom:6px;">${escapeHtml(top.career)}</div>
          <div style="color:var(--text-secondary);font-size:13px;margin-bottom:10px;">${escapeHtml(top.description)}</div>
          <div class="progress-bar"><div class="fill" style="width:${top.fit_score}%"></div></div>
          <div style="font-size:12px;color:var(--text-secondary);margin-top:6px;">${top.fit_score}% fit score</div>
        ` : `
          <p style="color:var(--text-secondary);font-size:14px;">Take the Career Assessment to discover your best-fit careers.</p>
          <button class="btn" onclick="goTo('assessment')">Start Assessment</button>
        `}
      </div>
      <div class="card">
        <h3 style="margin-bottom:14px;">🗺️ Learning Roadmap</h3>
        ${rp ? `
          <div style="font-size:16px;font-weight:600;margin-bottom:8px;">${escapeHtml(rp.career)}</div>
          <div class="progress-bar"><div class="fill" style="width:${rp.percent}%"></div></div>
          <div style="font-size:12px;color:var(--text-secondary);margin-top:6px;">${rp.done} of ${rp.total} topics completed</div>
          <button class="btn-ghost" style="margin-top:14px;" onclick="goTo('roadmap')">View Roadmap</button>
        ` : `
          <p style="color:var(--text-secondary);font-size:14px;">Generate a step-by-step roadmap for any career.</p>
          <button class="btn" onclick="goTo('roadmap')">Create Roadmap</button>
        `}
      </div>
    </div>
    <div class="card" style="margin-top:18px;">
      <h3 style="margin-bottom:10px;">Supported Careers</h3>
      <div class="tag-list">
        ${d.supported_careers.map(c => `<span class="skill-pill">${escapeHtml(c)}</span>`).join("")}
      </div>
    </div>
  `;
}

// ---------------------------------------------------------------------------
// Career Assessment page
// ---------------------------------------------------------------------------

function selectOption(qid, opt) {
  state.answers[qid] = opt;
  render();
}

async function submitAssessment() {
  if (Object.keys(state.answers).length < state.questions.length) {
    showToast("Please answer all questions first.", "error");
    return;
  }
  state.loading = true;
  render();
  try {
    const data = await api("/assessment/submit", { method: "POST", body: { answers: state.answers } });
    state.assessmentResults = data.best_career_options;
  } catch (err) {
    showToast(err.message, "error");
  } finally {
    state.loading = false;
    render();
  }
}

function retakeAssessment() {
  state.answers = {};
  state.assessmentResults = null;
  render();
}

function renderAssessment() {
  if (!state.questions) {
    return `<div class="page-header"><h1>Career Assessment Agent</h1></div><div class="card"><span class="spinner"></span> Loading questions...</div>`;
  }

  if (state.assessmentResults) {
    return `
      <div class="page-header">
        <h1>Your Career Matches 🎯</h1>
        <p>Based on a trait-similarity model using your answers.</p>
      </div>
      <div class="card">
        ${state.assessmentResults.map((r, i) => `
          <div class="career-result">
            <div class="rank">#${i + 1}</div>
            <div class="details">
              <h3>${escapeHtml(r.career)} — ${r.fit_score}% fit</h3>
              <p>${escapeHtml(r.description)}</p>
              <div class="tag-list">${r.core_skills.map(s => `<span class="skill-pill">${escapeHtml(s)}</span>`).join("")}</div>
              <div class="progress-bar"><div class="fill" style="width:${r.fit_score}%"></div></div>
              <p style="margin-top:6px;">💰 Avg salary: ${escapeHtml(r.avg_salary_inr)}</p>
            </div>
          </div>
        `).join("")}
        <button class="btn-ghost" onclick="retakeAssessment()" style="margin-top:10px;">Retake Assessment</button>
      </div>
    `;
  }

  return `
    <div class="page-header">
      <h1>Career Assessment Agent</h1>
      <p>Answer these ${state.questions.length} quick questions to discover your best-fit careers.</p>
    </div>
    <div class="card">
      ${state.questions.map((q, idx) => `
        <div style="margin-bottom:26px;">
          <h3 style="margin-bottom:12px;font-size:15px;">${idx + 1}. ${escapeHtml(q.question)}</h3>
          ${Object.entries(q.options).map(([key, label]) => `
            <button class="option-btn ${state.answers[q.id] === key ? "selected" : ""}"
              onclick="selectOption('${q.id}','${key}')">${escapeHtml(label)}</button>
          `).join("")}
        </div>
      `).join("")}
      <button class="btn" onclick="submitAssessment()" ${state.loading ? "disabled" : ""}>
        ${state.loading ? `<span class="spinner"></span>` : "See My Results"}
      </button>
    </div>
  `;
}

// ---------------------------------------------------------------------------
// Learning Roadmap page
// ---------------------------------------------------------------------------

async function createRoadmap() {
  const select = document.getElementById("roadmap-career-select");
  const career = select.value;
  state.loading = true;
  render();
  try {
    const data = await api("/roadmap/generate", { method: "POST", body: { career } });
    state.roadmap = { roadmap_id: data.roadmap_id, career: data.career, topics: data.topics };
    showToast(`Roadmap for ${career} created!`);
  } catch (err) {
    showToast(err.message, "error");
  } finally {
    state.loading = false;
    render();
  }
}

async function toggleTopic(topicId) {
  try {
    const data = await api(`/roadmap/${state.roadmap.roadmap_id}/toggle/${topicId}`, { method: "POST" });
    state.roadmap.topics = data.topics;
    render();
  } catch (err) {
    showToast(err.message, "error");
  }
}

function renderRoadmap() {
  return `
    <div class="page-header">
      <h1>Learning Roadmap Agent</h1>
      <p>Get a step-by-step checklist tailored to any supported career.</p>
    </div>
    <div class="card" style="margin-bottom:18px;">
      <div class="select-row">
        <select id="roadmap-career-select">
          ${state.roadmapCareers.map(c => `<option value="${escapeHtml(c)}" ${state.roadmap && state.roadmap.career === c ? "selected" : ""}>${escapeHtml(c)}</option>`).join("")}
        </select>
        <button class="btn" onclick="createRoadmap()" ${state.loading ? "disabled" : ""}>
          ${state.loading ? `<span class="spinner"></span>` : (state.roadmap ? "Generate New Roadmap" : "Generate Roadmap")}
        </button>
      </div>
    </div>
    ${state.roadmap ? `
      <div class="card">
        <h3 style="margin-bottom:6px;">${escapeHtml(state.roadmap.career)} Roadmap</h3>
        ${(() => {
          const done = state.roadmap.topics.filter(t => t.done).length;
          const total = state.roadmap.topics.length;
          const pct = total ? Math.round((done / total) * 100) : 0;
          return `
            <div class="progress-bar" style="margin-bottom:16px;"><div class="fill" style="width:${pct}%"></div></div>
            <p style="font-size:12px;color:var(--text-secondary);margin-bottom:16px;">${done} of ${total} topics completed (${pct}%)</p>
          `;
        })()}
        ${state.roadmap.topics.map(t => `
          <div class="roadmap-topic ${t.done ? "done" : ""}" onclick="toggleTopic(${t.id})">
            <div class="checkbox">${t.done ? "✓" : ""}</div>
            <span class="topic-title">${escapeHtml(t.title)}</span>
          </div>
        `).join("")}
      </div>
    ` : `
      <div class="card empty-state">
        <div class="icon">🗺️</div>
        <p>No roadmap yet — pick a career above and generate one.</p>
      </div>
    `}
  `;
}

// ---------------------------------------------------------------------------
// Resume Review page
// ---------------------------------------------------------------------------

async function submitResume() {
  const text = document.getElementById("resume-text").value.trim();
  const career = document.getElementById("resume-career-select").value;
  if (text.length < 20) {
    showToast("Please paste more of your resume text.", "error");
    return;
  }
  state.loading = true;
  render();
  try {
    const data = await api("/resume/review", { method: "POST", body: { resume_text: text, target_career: career || null } });
    state.resumeResult = data;
  } catch (err) {
    showToast(err.message, "error");
  } finally {
    state.loading = false;
    render();
  }
}

function renderResume() {
  const careers = Object.keys(CAREER_LIST);
  return `
    <div class="page-header">
      <h1>Resume Review Agent</h1>
      <p>Paste your resume text below for an instant heuristic score and feedback.</p>
    </div>
    <div class="grid grid-2">
      <div class="card">
        <div class="field">
          <label>Target Career (optional, improves keyword matching)</label>
          <select id="resume-career-select">
            <option value="">— None —</option>
            ${careers.map(c => `<option value="${escapeHtml(c)}">${escapeHtml(c)}</option>`).join("")}
          </select>
        </div>
        <div class="field">
          <label>Resume Text</label>
          <textarea id="resume-text" class="resume-input" placeholder="Paste your resume content here...">${state.resumeResult ? "" : ""}</textarea>
        </div>
        <button class="btn" onclick="submitResume()" ${state.loading ? "disabled" : ""}>
          ${state.loading ? `<span class="spinner"></span>` : "Review Resume"}
        </button>
      </div>
      <div class="card">
        ${state.resumeResult ? `
          <h3 style="margin-bottom:14px;">Score: ${state.resumeResult.score}/100</h3>
          <div class="progress-bar" style="margin-bottom:18px;"><div class="fill" style="width:${state.resumeResult.score}%"></div></div>
          <p style="font-size:13px;color:var(--text-secondary);margin-bottom:6px;">Word count: ${state.resumeResult.word_count}</p>
          <p style="font-size:13px;color:var(--text-secondary);margin-bottom:14px;">
            Contact info: ${state.resumeResult.has_contact_info ? "✅ Found" : "❌ Missing"} ·
            Quantified impact: ${state.resumeResult.has_quantified_impact ? "✅ Found" : "❌ Missing"}
          </p>
          <h4 style="margin-bottom:8px;font-size:14px;">Feedback</h4>
          <ul style="padding-left:18px;font-size:13px;color:var(--text-secondary);line-height:1.7;">
            ${state.resumeResult.feedback.map(f => `<li>${escapeHtml(f)}</li>`).join("")}
          </ul>
          ${state.resumeResult.matched_keywords && state.resumeResult.matched_keywords.length ? `
            <h4 style="margin:14px 0 8px;font-size:14px;">Matched Skills</h4>
            <div class="tag-list">${state.resumeResult.matched_keywords.map(k => `<span class="skill-pill">${escapeHtml(k)}</span>`).join("")}</div>
          ` : ""}
        ` : `
          <div class="empty-state">
            <div class="icon">📄</div>
            <p>Your review results will appear here.</p>
          </div>
        `}
      </div>
    </div>
  `;
}

// ---------------------------------------------------------------------------
// Career Chat page
// ---------------------------------------------------------------------------

async function sendChat() {
  const input = document.getElementById("chat-input");
  const message = input.value.trim();
  if (!message) return;
  input.value = "";
  state.chatLog.push({ role: "user", content: message });
  render();
  scrollChatToBottom();
  try {
    const data = await api("/chat/message", { method: "POST", body: { message } });
    state.chatLog.push({ role: "agent", content: data.reply });
  } catch (err) {
    state.chatLog.push({ role: "agent", content: `⚠️ ${err.message}` });
  } finally {
    render();
    scrollChatToBottom();
  }
}

function handleChatKey(e) {
  if (e.key === "Enter") sendChat();
}

function scrollChatToBottom() {
  requestAnimationFrame(() => {
    const win = document.getElementById("chat-window");
    if (win) win.scrollTop = win.scrollHeight;
  });
}

function renderChat() {
  return `
    <div class="page-header">
      <h1>Career Chat Agent</h1>
      <p>Ask about resumes, interviews, skills, salaries, or career transitions.</p>
    </div>
    <div class="card">
      <div class="chat-window" id="chat-window">
        ${state.chatLog.length === 0 ? `
          <div class="empty-state">
            <div class="icon">💬</div>
            <p>Say hi to get started!</p>
          </div>
        ` : state.chatLog.map(m => `
          <div class="chat-bubble ${m.role === "user" ? "user" : "agent"}">${escapeHtml(m.content)}</div>
        `).join("")}
      </div>
      <div class="chat-input-row">
        <input id="chat-input" type="text" placeholder="Type a message..." onkeydown="handleChatKey(event)" />
        <button class="btn" onclick="sendChat()">Send</button>
      </div>
    </div>
  `;
}

// ---------------------------------------------------------------------------
// Job Recommendation page
// ---------------------------------------------------------------------------

async function findJobs() {
  const career = document.getElementById("jobs-career-select").value;
  const skillsRaw = document.getElementById("jobs-skills-input").value;
  const skills = skillsRaw.split(",").map(s => s.trim()).filter(Boolean);
  state.loading = true;
  render();
  try {
    const data = await api("/jobs/recommend", { method: "POST", body: { career: career || null, skills } });
    state.jobResults = data.recommendations;
  } catch (err) {
    showToast(err.message, "error");
  } finally {
    state.loading = false;
    render();
  }
}

function renderJobs() {
  return `
    <div class="page-header">
      <h1>Job Recommendation Agent</h1>
      <p>Get matched job titles based on a career track and your skills.</p>
    </div>
    <div class="card" style="margin-bottom:18px;">
      <div class="select-row">
        <select id="jobs-career-select">
          <option value="">Use my latest assessment</option>
          ${state.jobCareers.map(c => `<option value="${escapeHtml(c)}">${escapeHtml(c)}</option>`).join("")}
        </select>
        <input id="jobs-skills-input" type="text" placeholder="Your skills, comma separated (e.g. Python, SQL)" style="flex:1;min-width:220px;" />
        <button class="btn" onclick="findJobs()" ${state.loading ? "disabled" : ""}>
          ${state.loading ? `<span class="spinner"></span>` : "Find Jobs"}
        </button>
      </div>
    </div>
    ${state.jobResults ? `
      <div class="grid grid-3">
        ${state.jobResults.map(j => `
          <div class="card job-card">
            <div class="top">
              <div>
                <h3>${escapeHtml(j.title)}</h3>
                <span class="level-tag">${escapeHtml(j.level)}</span>
              </div>
              <div class="match-badge">${j.match_score}%</div>
            </div>
            <p style="font-size:12px;color:var(--text-secondary);margin:8px 0 4px;">${escapeHtml(j.career)}</p>
            <div class="tag-list">${j.required_skills.map(s => `<span class="skill-pill">${escapeHtml(s)}</span>`).join("")}</div>
          </div>
        `).join("")}
      </div>
    ` : `
      <div class="card empty-state">
        <div class="icon">💼</div>
        <p>Choose a career (or use your assessment) and hit "Find Jobs".</p>
      </div>
    `}
  `;
}

// ---------------------------------------------------------------------------
// Profile page
// ---------------------------------------------------------------------------

async function saveProfile() {
  const name = document.getElementById("profile-name").value.trim();
  const bio = document.getElementById("profile-bio").value.trim();
  try {
    const data = await api("/profile", { method: "PUT", body: { name, bio } });
    state.user = data.user;
    localStorage.setItem("cp_user", JSON.stringify(data.user));
    showToast("Profile updated!");
    render();
  } catch (err) {
    showToast(err.message, "error");
  }
}

function renderProfile() {
  const u = state.user;
  return `
    <div class="page-header">
      <h1>Profile</h1>
      <p>Manage your account information.</p>
    </div>
    <div class="card" style="max-width:480px;">
      <div class="field">
        <label>Name</label>
        <input id="profile-name" type="text" value="${escapeHtml(u.name)}" />
      </div>
      <div class="field">
        <label>Email</label>
        <input type="text" value="${escapeHtml(u.email)}" disabled />
      </div>
      <div class="field">
        <label>Bio</label>
        <textarea id="profile-bio" rows="4">${escapeHtml(u.bio || "")}</textarea>
      </div>
      <button class="btn" onclick="saveProfile()">Save Changes</button>
      <button class="btn-ghost" style="margin-left:10px;" onclick="logout()">Log Out</button>
    </div>
  `;
}

// ---------------------------------------------------------------------------
// Shell / layout
// ---------------------------------------------------------------------------

function escapeHtml(str) {
  if (str === null || str === undefined) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

const CAREER_LIST = {
  "Software Engineer": 1, "Data Scientist": 1, "UI/UX Designer": 1, "Product Manager": 1,
  "Digital Marketer": 1, "Business Analyst": 1, "Cybersecurity Analyst": 1,
  "Content Writer": 1, "HR Manager": 1, "Sales Executive": 1,
};

function renderAuthScreen() {
  const isLogin = state.authMode === "login";
  return `
    <div class="auth-wrap">
      <div class="card auth-card">
        <div class="auth-logo">
          <div class="mark">🧭</div>
          <span>Multi Agent Mentor</span>
        </div>
        <h2 style="margin-bottom:4px;">${isLogin ? "Welcome back" : "Create your account"}</h2>
        <p style="color:var(--text-secondary);font-size:13px;margin-bottom:20px;">
          ${isLogin ? "Log in to continue your career journey." : "Start your personalized career journey."}
        </p>
        <div id="auth-error" class="auth-error" style="display:none;"></div>
        <form id="auth-form">
          ${isLogin ? `
            <div class="field">
              <label>Email</label>
              <input id="login-email" type="email" required placeholder="you@example.com" />
            </div>
            <div class="field">
              <label>Password</label>
              <input id="login-password" type="password" required placeholder="••••••••" />
            </div>
          ` : `
            <div class="field">
              <label>Full Name</label>
              <input id="reg-name" type="text" required placeholder="Jane Doe" />
            </div>
            <div class="field">
              <label>Email</label>
              <input id="reg-email" type="email" required placeholder="you@example.com" />
            </div>
            <div class="field">
              <label>Password</label>
              <input id="reg-password" type="password" required placeholder="At least 4 characters" />
            </div>
          `}
          <button id="auth-submit-btn" type="submit" class="btn" style="width:100%;margin-top:6px;">
            ${isLogin ? "Log In" : "Create Account"}
          </button>
        </form>
        <div class="auth-toggle">
          ${isLogin ? `Don't have an account? <a onclick="toggleAuthMode()">Sign up</a>`
                    : `Already have an account? <a onclick="toggleAuthMode()">Log in</a>`}
        </div>
      </div>
    </div>
  `;
}

function renderShell() {
  const pageRenderers = {
    dashboard: renderDashboard,
    assessment: renderAssessment,
    roadmap: renderRoadmap,
    resume: renderResume,
    chat: renderChat,
    jobs: renderJobs,
    profile: renderProfile,
  };
  const initials = state.user.name.split(" ").map(w => w[0]).slice(0, 2).join("").toUpperCase();

  return `
    <div class="layout">
      <div class="sidebar">
        <div class="logo"><div class="mark">🧭</div><span>Multi Agent Mentor</span></div>
        <nav>
          ${NAV_ITEMS.map(item => `
            <button class="nav-link ${state.page === item.id ? "active" : ""}" onclick="goTo('${item.id}')">
              <span class="icon">${item.icon}</span> ${item.label}
            </button>
          `).join("")}
        </nav>
        <div class="sidebar-footer">
          <div class="user-chip">
            <div class="avatar">${initials}</div>
            <div class="info">
              <div class="name">${escapeHtml(state.user.name)}</div>
              <div class="email">${escapeHtml(state.user.email)}</div>
            </div>
          </div>
          <button class="btn-ghost" style="width:100%;" onclick="logout()">Log Out</button>
        </div>
      </div>
      <div class="main">
        ${pageRenderers[state.page] ? pageRenderers[state.page]() : renderDashboard()}
      </div>
    </div>
  `;
}

function render() {
  const app = document.getElementById("app");
  if (!state.token || !state.user) {
    app.innerHTML = renderAuthScreen();
    const form = document.getElementById("auth-form");
    if (form) form.addEventListener("submit", handleAuthSubmit);
  } else {
    app.innerHTML = renderShell();
  }
}

// ---------------------------------------------------------------------------
// Init
// ---------------------------------------------------------------------------

render();
if (state.token && state.user) {
  loadPageData(state.page);
}
