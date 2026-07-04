"""
Static, rule-based knowledge base for Multi Agent Mentor.
No external API keys or ML models required — everything here is
plain Python data + heuristics so the app runs 100% locally.
"""

# ---------------------------------------------------------------------------
# 1. Career Assessment Agent data
# ---------------------------------------------------------------------------

# Each question maps an option letter -> trait deltas.
ASSESSMENT_QUESTIONS = [
    {
        "id": "q1",
        "question": "Which activity sounds most enjoyable to you?",
        "options": {
            "A": {"label": "Solving logic puzzles or debugging a problem", "traits": {"analytical": 3, "technical": 2}},
            "B": {"label": "Designing something visually beautiful", "traits": {"creative": 3, "design": 2}},
            "C": {"label": "Persuading a group to support an idea", "traits": {"social": 2, "leadership": 3}},
            "D": {"label": "Organizing a plan and tracking progress", "traits": {"organized": 3, "leadership": 1}},
        },
    },
    {
        "id": "q2",
        "question": "Pick the school subject you liked most.",
        "options": {
            "A": {"label": "Mathematics / Computer Science", "traits": {"analytical": 3, "technical": 3}},
            "B": {"label": "Art / Literature", "traits": {"creative": 3}},
            "C": {"label": "Economics / Business Studies", "traits": {"leadership": 2, "organized": 2}},
            "D": {"label": "Psychology / Communication", "traits": {"social": 3}},
        },
    },
    {
        "id": "q3",
        "question": "In a group project, you usually end up...",
        "options": {
            "A": {"label": "Writing the code / building the technical piece", "traits": {"technical": 3, "analytical": 1}},
            "B": {"label": "Making the slides look great", "traits": {"creative": 2, "design": 3}},
            "C": {"label": "Leading the discussion and assigning tasks", "traits": {"leadership": 3}},
            "D": {"label": "Talking to users/clients to gather feedback", "traits": {"social": 3}},
        },
    },
    {
        "id": "q4",
        "question": "Which work environment excites you most?",
        "options": {
            "A": {"label": "Quiet, focused, deep-work environment", "traits": {"analytical": 2, "technical": 2}},
            "B": {"label": "Fast-paced, ever-changing, people-facing", "traits": {"social": 2, "leadership": 2}},
            "C": {"label": "Creative studio with lots of visual work", "traits": {"creative": 3, "design": 2}},
            "D": {"label": "Structured environment with clear processes", "traits": {"organized": 3}},
        },
    },
    {
        "id": "q5",
        "question": "What motivates you most in a job?",
        "options": {
            "A": {"label": "Building things that work perfectly", "traits": {"technical": 3, "analytical": 1}},
            "B": {"label": "Making something people find beautiful/useful to look at", "traits": {"design": 3, "creative": 1}},
            "C": {"label": "Growing a team or business", "traits": {"leadership": 3}},
            "D": {"label": "Helping and connecting with people", "traits": {"social": 3}},
        },
    },
    {
        "id": "q6",
        "question": "Which of these tasks would you pick first from a to-do list?",
        "options": {
            "A": {"label": "Analyze a dataset to find a trend", "traits": {"analytical": 3}},
            "B": {"label": "Sketch a new app screen", "traits": {"design": 3, "creative": 1}},
            "C": {"label": "Write a security checklist", "traits": {"technical": 2, "organized": 2}},
            "D": {"label": "Write a marketing caption", "traits": {"creative": 2, "social": 2}},
        },
    },
    {
        "id": "q7",
        "question": "How do you prefer to communicate at work?",
        "options": {
            "A": {"label": "Detailed written documentation", "traits": {"organized": 2, "technical": 1}},
            "B": {"label": "Visual mockups / diagrams", "traits": {"design": 3}},
            "C": {"label": "Live conversations and pitches", "traits": {"social": 2, "leadership": 2}},
            "D": {"label": "Data / reports with numbers", "traits": {"analytical": 3}},
        },
    },
]

# Career trait profiles (ideal vector) + metadata used across agents.
CAREER_PROFILES = {
    "Software Engineer": {
        "traits": {"analytical": 3, "technical": 3, "organized": 1},
        "description": "Designs, builds and maintains software systems and applications.",
        "core_skills": ["Python", "Data Structures", "Git", "APIs", "Problem Solving", "SQL"],
        "avg_salary_inr": "6-18 LPA",
    },
    "Data Scientist": {
        "traits": {"analytical": 3, "technical": 2, "organized": 1},
        "description": "Extracts insights from data using statistics, ML and visualization.",
        "core_skills": ["Python", "Statistics", "Machine Learning", "SQL", "Data Visualization", "Pandas"],
        "avg_salary_inr": "7-20 LPA",
    },
    "UI/UX Designer": {
        "traits": {"design": 3, "creative": 3},
        "description": "Crafts intuitive, visually appealing digital experiences for users.",
        "core_skills": ["Figma", "Wireframing", "User Research", "Prototyping", "Design Systems"],
        "avg_salary_inr": "5-14 LPA",
    },
    "Product Manager": {
        "traits": {"leadership": 3, "organized": 2, "social": 1},
        "description": "Owns product strategy and coordinates teams to deliver value to users.",
        "core_skills": ["Roadmapping", "Stakeholder Management", "Analytics", "Communication", "Agile"],
        "avg_salary_inr": "10-25 LPA",
    },
    "Digital Marketer": {
        "traits": {"creative": 2, "social": 3},
        "description": "Grows brand reach and revenue through digital campaigns and content.",
        "core_skills": ["SEO", "Content Strategy", "Social Media", "Analytics", "Copywriting"],
        "avg_salary_inr": "4-12 LPA",
    },
    "Business Analyst": {
        "traits": {"analytical": 2, "organized": 3},
        "description": "Bridges business needs and technical solutions using data and process analysis.",
        "core_skills": ["Excel", "SQL", "Requirement Gathering", "Process Mapping", "Communication"],
        "avg_salary_inr": "5-14 LPA",
    },
    "Cybersecurity Analyst": {
        "traits": {"technical": 3, "analytical": 2, "organized": 1},
        "description": "Protects systems and networks from digital threats and breaches.",
        "core_skills": ["Networking", "Linux", "Security Tools", "Risk Assessment", "Ethical Hacking Basics"],
        "avg_salary_inr": "6-16 LPA",
    },
    "Content Writer": {
        "traits": {"creative": 3, "social": 1},
        "description": "Creates engaging written content for brands, products and audiences.",
        "core_skills": ["Writing", "SEO Basics", "Research", "Editing", "Storytelling"],
        "avg_salary_inr": "3-9 LPA",
    },
    "HR Manager": {
        "traits": {"social": 3, "leadership": 2, "organized": 1},
        "description": "Manages people operations, hiring, culture and employee growth.",
        "core_skills": ["Recruitment", "Communication", "Conflict Resolution", "Labor Law Basics", "Onboarding"],
        "avg_salary_inr": "5-14 LPA",
    },
    "Sales Executive": {
        "traits": {"social": 3, "leadership": 2},
        "description": "Builds relationships and drives revenue by closing deals with clients.",
        "core_skills": ["Negotiation", "CRM Tools", "Communication", "Lead Generation", "Presentation"],
        "avg_salary_inr": "4-12 LPA",
    },
}

# ---------------------------------------------------------------------------
# 2. Learning Roadmap Agent data
# ---------------------------------------------------------------------------

ROADMAPS = {
    "Software Engineer": [
        "Learn a programming language (Python/Java)",
        "Master Data Structures & Algorithms",
        "Understand Git & version control",
        "Learn SQL & databases",
        "Build 2-3 full-stack projects",
        "Learn REST APIs",
        "Practice DSA on coding platforms",
        "Prepare for technical interviews",
    ],
    "Data Scientist": [
        "Learn Python for data analysis",
        "Study statistics & probability",
        "Master Pandas & NumPy",
        "Learn data visualization (Matplotlib/Seaborn)",
        "Study Machine Learning fundamentals",
        "Learn SQL for data querying",
        "Build 2 end-to-end ML projects",
        "Learn to communicate insights via dashboards",
    ],
    "UI/UX Designer": [
        "Learn design fundamentals (color, typography, layout)",
        "Master Figma",
        "Learn user research methods",
        "Study wireframing & prototyping",
        "Build a case study portfolio (3 projects)",
        "Learn design systems",
        "Get feedback via design communities",
        "Apply for internships/junior roles",
    ],
    "Product Manager": [
        "Understand product lifecycle & Agile/Scrum",
        "Learn to write PRDs & user stories",
        "Study market & competitor analysis",
        "Learn analytics tools (Mixpanel/GA)",
        "Practice stakeholder communication",
        "Build a mock product case study",
        "Learn roadmap prioritization frameworks",
        "Network with PMs / seek mentorship",
    ],
    "Digital Marketer": [
        "Learn SEO fundamentals",
        "Study content marketing & copywriting",
        "Learn social media strategy",
        "Get familiar with Google Analytics",
        "Run a small ad campaign (practice budget)",
        "Learn email marketing basics",
        "Build a personal brand/portfolio",
        "Get a certification (Google/HubSpot)",
    ],
    "Business Analyst": [
        "Master Excel & data analysis basics",
        "Learn SQL fundamentals",
        "Study requirement gathering techniques",
        "Learn process mapping (BPMN)",
        "Practice with real datasets/case studies",
        "Learn basic Power BI/Tableau",
        "Build a business case study project",
        "Prepare for BA interviews",
    ],
    "Cybersecurity Analyst": [
        "Learn networking fundamentals",
        "Get comfortable with Linux",
        "Study common attack types & defenses",
        "Learn security tools (Wireshark, Nmap)",
        "Understand risk assessment basics",
        "Try beginner CTF challenges",
        "Learn about compliance basics (ISO/GDPR)",
        "Pursue a foundational certification (Security+)",
    ],
    "Content Writer": [
        "Practice daily writing",
        "Learn SEO writing basics",
        "Study different content formats (blogs, scripts, ads)",
        "Build a writing portfolio (5+ samples)",
        "Learn editing & proofreading skills",
        "Understand audience & tone adaptation",
        "Pitch to publications/freelance platforms",
        "Build a personal blog/newsletter",
    ],
    "HR Manager": [
        "Learn recruitment & sourcing basics",
        "Study labor law fundamentals",
        "Learn employee engagement strategies",
        "Practice interview & onboarding processes",
        "Study conflict resolution techniques",
        "Learn HR tools (HRMS basics)",
        "Get an HR certification (SHRM/CHRP)",
        "Build case studies of HR initiatives",
    ],
    "Sales Executive": [
        "Learn sales fundamentals & pipeline stages",
        "Practice cold outreach & pitching",
        "Learn negotiation techniques",
        "Get familiar with CRM tools (HubSpot/Salesforce)",
        "Study objection handling",
        "Practice mock sales calls",
        "Learn to read sales metrics/KPIs",
        "Build a personal sales playbook",
    ],
}

# ---------------------------------------------------------------------------
# 3. Job Recommendation Agent data
# ---------------------------------------------------------------------------

JOB_TITLES = {
    "Software Engineer": [
        {"title": "Junior Software Engineer", "level": "Entry", "skills": ["Python", "Git", "SQL"]},
        {"title": "Backend Developer", "level": "Mid", "skills": ["APIs", "Databases", "Python"]},
        {"title": "Full-Stack Developer", "level": "Mid", "skills": ["React", "Node.js", "SQL"]},
    ],
    "Data Scientist": [
        {"title": "Data Analyst", "level": "Entry", "skills": ["SQL", "Excel", "Data Visualization"]},
        {"title": "Junior Data Scientist", "level": "Entry", "skills": ["Python", "Statistics", "Machine Learning"]},
        {"title": "ML Engineer", "level": "Mid", "skills": ["Machine Learning", "Python", "Pandas"]},
    ],
    "UI/UX Designer": [
        {"title": "Junior UX Designer", "level": "Entry", "skills": ["Figma", "Wireframing"]},
        {"title": "Product Designer", "level": "Mid", "skills": ["Prototyping", "User Research", "Design Systems"]},
        {"title": "UI Designer", "level": "Entry", "skills": ["Figma", "Typography"]},
    ],
    "Product Manager": [
        {"title": "Associate Product Manager", "level": "Entry", "skills": ["Roadmapping", "Analytics"]},
        {"title": "Product Manager", "level": "Mid", "skills": ["Stakeholder Management", "Agile"]},
    ],
    "Digital Marketer": [
        {"title": "SEO Executive", "level": "Entry", "skills": ["SEO", "Content Strategy"]},
        {"title": "Social Media Manager", "level": "Entry", "skills": ["Social Media", "Copywriting"]},
        {"title": "Digital Marketing Manager", "level": "Mid", "skills": ["Analytics", "SEO", "Content Strategy"]},
    ],
    "Business Analyst": [
        {"title": "Junior Business Analyst", "level": "Entry", "skills": ["Excel", "SQL"]},
        {"title": "Business Analyst", "level": "Mid", "skills": ["Requirement Gathering", "Process Mapping"]},
    ],
    "Cybersecurity Analyst": [
        {"title": "SOC Analyst", "level": "Entry", "skills": ["Networking", "Security Tools"]},
        {"title": "Cybersecurity Analyst", "level": "Mid", "skills": ["Risk Assessment", "Linux"]},
    ],
    "Content Writer": [
        {"title": "Junior Content Writer", "level": "Entry", "skills": ["Writing", "Research"]},
        {"title": "SEO Content Writer", "level": "Entry", "skills": ["SEO Basics", "Writing"]},
    ],
    "HR Manager": [
        {"title": "HR Executive", "level": "Entry", "skills": ["Recruitment", "Communication"]},
        {"title": "HR Business Partner", "level": "Mid", "skills": ["Employee Relations", "Onboarding"]},
    ],
    "Sales Executive": [
        {"title": "Sales Development Rep", "level": "Entry", "skills": ["Lead Generation", "Communication"]},
        {"title": "Account Executive", "level": "Mid", "skills": ["Negotiation", "CRM Tools"]},
    ],
}

# ---------------------------------------------------------------------------
# 4. Resume Review Agent data
# ---------------------------------------------------------------------------

RESUME_REQUIRED_SECTIONS = ["experience", "education", "skills", "projects", "summary"]
RESUME_CONTACT_KEYWORDS = ["email", "@", "phone", "linkedin"]
RESUME_ACTION_VERBS = [
    "built", "led", "managed", "developed", "designed", "created", "improved",
    "increased", "reduced", "launched", "implemented", "optimized", "analyzed",
    "coordinated", "delivered",
]

# ---------------------------------------------------------------------------
# 5. Career Chat Agent data (rule-based keyword FAQ)
# ---------------------------------------------------------------------------

CHAT_RULES = [
    (["resume", "cv"], "A strong resume highlights measurable achievements with action verbs (e.g. 'Increased sign-ups by 20%'), keeps to 1 page for freshers, and includes Skills, Projects, Experience and Education sections. Try the Resume Review Agent to get a score!"),
    (["interview"], "For interviews: research the company, prepare 2-3 STAR-format stories about your achievements, practice common questions out loud, and prepare thoughtful questions to ask the interviewer."),
    (["salary", "pay", "compensation"], "Salary depends on role, location, and experience. Check the Career Assessment and Job Recommendation agents — they show typical salary ranges for matched careers."),
    (["skill", "learn", "upskill"], "The best way to upskill is to pick ONE target role, then follow a structured roadmap — check out the Learning Roadmap Agent to get a step-by-step plan tailored to a career."),
    (["switch", "change career", "transition"], "Career transitions work best when you map your transferable skills to the new field, build 1-2 portfolio projects in the new domain, and network with people already in that role."),
    (["job", "hiring", "opportunit"], "Head over to the Job Recommendation Agent — it suggests roles that match your assessed career profile along with the core skills each role expects."),
    (["assessment", "test", "quiz"], "The Career Assessment Agent asks you a short set of questions about your interests and working style, then matches you to careers using a trait-based scoring model."),
    (["roadmap", "plan", "path"], "The Learning Roadmap Agent generates a step-by-step checklist for any of our 10 supported careers — you can check off topics as you complete them."),
    (["hello", "hi", "hey"], "Hi there! I'm your Career Chat Agent. Ask me about resumes, interviews, skills, salaries, or career transitions."),
    (["thank"], "You're welcome! Good luck with your career journey. Let me know if you have more questions."),
]
CHAT_FALLBACK = "That's a great question. I can help most with resumes, interviews, skills to learn, job roles, and career transitions — try asking about one of those, or explore the other agents in the sidebar!"
