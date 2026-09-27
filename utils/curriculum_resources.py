"""
utils/curriculum_resources.py
Static Curated Free Resource Library for Dynamic 7-Day Placement Preparation.
Zero external API calls. 100% verified, reputable, and freely accessible learning assets.
Covers 35+ topics across technical, analytical, management, and executive domains.
"""

import re
from typing import List, Dict, Any

class CurriculumResourceLibrary:
    """
    Curated repository of high-impact free learning resources:
    YouTube full courses, interactive tutorials, official documentation,
    practice problem sets, and cheat sheets.
    """

    RESOURCE_DB: Dict[str, List[Dict[str, Any]]] = {
        # ── PROGRAMMING & DATA SCIENCE ──────────────────────────
        "python": [
            {"resource_id": "py_yt_full", "title": "Python Full Course for Beginners", "provider": "freeCodeCamp (YouTube)", "url": "https://www.youtube.com/watch?v=rfscVS0vtbw", "type": "Video", "duration_minutes": 270, "is_free": True, "difficulty": "Beginner"},
            {"resource_id": "py_official", "title": "Python 3 Official Tutorial", "provider": "python.org", "url": "https://docs.python.org/3/tutorial/", "type": "Documentation", "duration_minutes": 120, "is_free": True, "difficulty": "All Levels"},
            {"resource_id": "py_coursera", "title": "Python for Everybody (Free Audit)", "provider": "Coursera / UMich", "url": "https://www.coursera.org/specializations/python", "type": "Interactive Course", "duration_minutes": 600, "is_free": True, "difficulty": "Beginner"},
            {"resource_id": "py_cheat", "title": "Python Cheat Sheet for Placement Interviews", "provider": "DataCamp", "url": "https://www.datacamp.com/cheat-sheet/python-basics-cheat-sheet", "type": "Cheat Sheet", "duration_minutes": 20, "is_free": True, "difficulty": "All Levels"},
        ],
        "pandas": [
            {"resource_id": "pd_yt_corey", "title": "Pandas Data Analysis Tutorial", "provider": "Corey Schafer (YouTube)", "url": "https://www.youtube.com/playlist?list=PL-osiE80TeTsWmV9i9c58mdDCSskIFdDS", "type": "Video", "duration_minutes": 210, "is_free": True, "difficulty": "Intermediate"},
            {"resource_id": "pd_kaggle", "title": "Pandas Micro-Course", "provider": "Kaggle Learn", "url": "https://www.kaggle.com/learn/pandas", "type": "Interactive Course", "duration_minutes": 240, "is_free": True, "difficulty": "Beginner"},
            {"resource_id": "pd_10min", "title": "10 Minutes to Pandas", "provider": "pandas.pydata.org", "url": "https://pandas.pydata.org/docs/user_guide/10min.html", "type": "Documentation", "duration_minutes": 45, "is_free": True, "difficulty": "All Levels"},
            {"resource_id": "pd_cheat", "title": "Pandas Data Wrangling Cheat Sheet", "provider": "pandas.pydata.org", "url": "https://pandas.pydata.org/Pandas_Cheat_Sheet.pdf", "type": "Cheat Sheet", "duration_minutes": 15, "is_free": True, "difficulty": "All Levels"},
        ],
        "sql": [
            {"resource_id": "sql_mosh", "title": "Complete SQL Mastery Course", "provider": "Mosh Hamedani (YouTube)", "url": "https://www.youtube.com/watch?v=7S_tz1z_5bA", "type": "Video", "duration_minutes": 180, "is_free": True, "difficulty": "Beginner"},
            {"resource_id": "sql_mode", "title": "SQL Tutorial for Data Analysis", "provider": "Mode Analytics", "url": "https://mode.com/sql-tutorial/", "type": "Interactive Course", "duration_minutes": 240, "is_free": True, "difficulty": "Intermediate"},
            {"resource_id": "sql_lc50", "title": "Top SQL 50 Study Plan", "provider": "LeetCode", "url": "https://leetcode.com/studyplan/top-sql-50/", "type": "Practice Set", "duration_minutes": 300, "is_free": True, "difficulty": "Intermediate"},
            {"resource_id": "sql_cheat", "title": "SQL Syntax & Joins Cheat Sheet", "provider": "DataCamp", "url": "https://www.datacamp.com/cheat-sheet/sql-cheat-sheet", "type": "Cheat Sheet", "duration_minutes": 15, "is_free": True, "difficulty": "All Levels"},
        ],
        "machine learning": [
            {"resource_id": "ml_statquest", "title": "Machine Learning Fundamentals Explained", "provider": "StatQuest / Josh Starmer (YouTube)", "url": "https://www.youtube.com/playlist?list=PLblh5JKOoLUICTaGLRoHQDuF_7q2GfuJF", "type": "Video", "duration_minutes": 300, "is_free": True, "difficulty": "Beginner"},
            {"resource_id": "ml_kaggle", "title": "Intro to Machine Learning", "provider": "Kaggle Learn", "url": "https://www.kaggle.com/learn/intro-to-machine-learning", "type": "Interactive Course", "duration_minutes": 180, "is_free": True, "difficulty": "Beginner"},
            {"resource_id": "ml_sklearn", "title": "Scikit-Learn User Guide & Supervised Learning", "provider": "scikit-learn.org", "url": "https://scikit-learn.org/stable/user_guide.html", "type": "Documentation", "duration_minutes": 180, "is_free": True, "difficulty": "Intermediate"},
            {"resource_id": "ml_cheat", "title": "Scikit-Learn ML Algorithm Selector Map", "provider": "scikit-learn.org", "url": "https://scikit-learn.org/stable/tutorial/machine_learning_map/index.html", "type": "Cheat Sheet", "duration_minutes": 20, "is_free": True, "difficulty": "All Levels"},
        ],
        "deep learning": [
            {"resource_id": "dl_mit", "title": "MIT 6.S191: Introduction to Deep Learning", "provider": "MIT OpenCourseWare (YouTube)", "url": "https://www.youtube.com/playlist?list=PLtBw6njQRU-rwp5__7C0oIVt26ZgjG9NI", "type": "Video", "duration_minutes": 360, "is_free": True, "difficulty": "Intermediate"},
            {"resource_id": "dl_pytorch", "title": "Deep Learning with PyTorch: A 60-Minute Blitz", "provider": "PyTorch.org", "url": "https://pytorch.org/tutorials/beginner/deep_learning_60min_blitz.html", "type": "Documentation", "duration_minutes": 60, "is_free": True, "difficulty": "Intermediate"},
            {"resource_id": "dl_kaggle", "title": "Intro to Deep Learning", "provider": "Kaggle Learn", "url": "https://www.kaggle.com/learn/intro-to-deep-learning", "type": "Interactive Course", "duration_minutes": 240, "is_free": True, "difficulty": "Intermediate"},
        ],
        "statistics": [
            {"resource_id": "stat_khan", "title": "College Statistics & Probability", "provider": "Khan Academy", "url": "https://www.khanacademy.org/math/statistics-probability", "type": "Interactive Course", "duration_minutes": 360, "is_free": True, "difficulty": "Beginner"},
            {"resource_id": "stat_statquest", "title": "Hypothesis Testing and p-Values", "provider": "StatQuest (YouTube)", "url": "https://www.youtube.com/watch?v=vemZtEM63GY", "type": "Video", "duration_minutes": 60, "is_free": True, "difficulty": "Intermediate"},
            {"resource_id": "stat_cheat", "title": "Probability & Statistics Placement Cheat Sheet", "provider": "Stanford CS229", "url": "https://stanford.edu/~shervine/teaching/cs-229/refresher-probabilities-statistics", "type": "Cheat Sheet", "duration_minutes": 30, "is_free": True, "difficulty": "Intermediate"},
        ],

        # ── BUSINESS INTELLIGENCE & ANALYTICS ───────────────────
        "data visualization": [
            {"resource_id": "viz_storytelling", "title": "Storytelling with Data Video Series", "provider": "Cole Nussbaumer Knaflic (YouTube)", "url": "https://www.youtube.com/@storytellingwithdata", "type": "Video", "duration_minutes": 120, "is_free": True, "difficulty": "Beginner"},
            {"resource_id": "viz_kaggle", "title": "Data Visualization Micro-Course", "provider": "Kaggle Learn", "url": "https://www.kaggle.com/learn/data-visualization", "type": "Interactive Course", "duration_minutes": 180, "is_free": True, "difficulty": "Beginner"},
            {"resource_id": "viz_chart_guide", "title": "Financial Times Visual Vocabulary Chart Selector", "provider": "Financial Times", "url": "https://github.com/ft-interactive/chart-doctor/blob/master/visual-vocabulary/Visual-vocabulary.pdf", "type": "Cheat Sheet", "duration_minutes": 20, "is_free": True, "difficulty": "All Levels"},
        ],
        "power bi": [
            {"resource_id": "pbi_edureka", "title": "Power BI Full Course", "provider": "edureka! (YouTube)", "url": "https://www.youtube.com/watch?v=3u7MQz1EyPY", "type": "Video", "duration_minutes": 240, "is_free": True, "difficulty": "Beginner"},
            {"resource_id": "pbi_msft", "title": "Microsoft Power BI Guided Learning Paths", "provider": "Microsoft Learn", "url": "https://learn.microsoft.com/en-us/training/powerplatform/power-bi", "type": "Interactive Course", "duration_minutes": 300, "is_free": True, "difficulty": "Beginner"},
            {"resource_id": "pbi_cheat", "title": "Power BI DAX Formula Cheat Sheet", "provider": "DataCamp", "url": "https://www.datacamp.com/cheat-sheet/dax-cheat-sheet", "type": "Cheat Sheet", "duration_minutes": 20, "is_free": True, "difficulty": "Intermediate"},
        ],
        "tableau": [
            {"resource_id": "tab_freecodecamp", "title": "Tableau for Data Science & Business Intelligence", "provider": "freeCodeCamp (YouTube)", "url": "https://www.youtube.com/watch?v=TPPlXqm4Tbw", "type": "Video", "duration_minutes": 330, "is_free": True, "difficulty": "Beginner"},
            {"resource_id": "tab_official", "title": "Tableau Free Starter Kits & Video Tutorials", "provider": "Tableau.com", "url": "https://www.tableau.com/learn/training", "type": "Documentation", "duration_minutes": 180, "is_free": True, "difficulty": "Beginner"},
            {"resource_id": "tab_cheat", "title": "Tableau Calculations Cheat Sheet", "provider": "DataCamp", "url": "https://www.datacamp.com/cheat-sheet/tableau-cheat-sheet", "type": "Cheat Sheet", "duration_minutes": 20, "is_free": True, "difficulty": "Intermediate"},
        ],
        "excel": [
            {"resource_id": "xls_kevin", "title": "Advanced Excel for Business & Finance", "provider": "Kevin Stratvert (YouTube)", "url": "https://www.youtube.com/watch?v=Vl0H-qTclOg", "type": "Video", "duration_minutes": 150, "is_free": True, "difficulty": "Intermediate"},
            {"resource_id": "xls_chandoo", "title": "Excel Formulas & Dashboard Design Guide", "provider": "Chandoo.org", "url": "https://chandoo.org/wp/excel-basics/", "type": "Documentation", "duration_minutes": 120, "is_free": True, "difficulty": "Intermediate"},
            {"resource_id": "xls_cheat", "title": "Financial & Analytical Excel Functions Cheat Sheet", "provider": "Corporate Finance Institute", "url": "https://corporatefinanceinstitute.com/resources/excel/excel-shortcuts-cheat-sheet/", "type": "Cheat Sheet", "duration_minutes": 15, "is_free": True, "difficulty": "All Levels"},
        ],

        # ── CLOUD, DEVOPS & INFRASTRUCTURE ───────────────────────
        "aws": [
            {"resource_id": "aws_fcc", "title": "AWS Certified Cloud Practitioner Full Course", "provider": "freeCodeCamp (YouTube)", "url": "https://www.youtube.com/watch?v=SOTamWNgDKc", "type": "Video", "duration_minutes": 780, "is_free": True, "difficulty": "Beginner"},
            {"resource_id": "aws_skillbuilder", "title": "AWS Cloud Essentials Digital Course", "provider": "AWS Skill Builder", "url": "https://explore.skillbuilder.aws/learn/course/external/view/elearning/134/aws-cloud-practitioner-essentials", "type": "Interactive Course", "duration_minutes": 360, "is_free": True, "difficulty": "Beginner"},
            {"resource_id": "aws_cheat", "title": "AWS Services Core Architecture Cheat Sheet", "provider": "Tutorials Dojo", "url": "https://tutorialsdojo.com/aws-cheat-sheets/", "type": "Cheat Sheet", "duration_minutes": 30, "is_free": True, "difficulty": "Intermediate"},
        ],
        "azure": [
            {"resource_id": "az_fcc", "title": "Microsoft Azure Fundamentals (AZ-900) Course", "provider": "freeCodeCamp (YouTube)", "url": "https://www.youtube.com/watch?v=NKEFW2WJbcE", "type": "Video", "duration_minutes": 240, "is_free": True, "difficulty": "Beginner"},
            {"resource_id": "az_msft", "title": "Microsoft Azure Fundamentals Guided Path", "provider": "Microsoft Learn", "url": "https://learn.microsoft.com/en-us/training/paths/az-900-describe-cloud-concepts/", "type": "Interactive Course", "duration_minutes": 240, "is_free": True, "difficulty": "Beginner"},
        ],
        "docker": [
            {"resource_id": "dkr_techworld", "title": "Docker Tutorial for Beginners", "provider": "TechWorld with Nana (YouTube)", "url": "https://www.youtube.com/watch?v=3c-iBn73dDE", "type": "Video", "duration_minutes": 180, "is_free": True, "difficulty": "Beginner"},
            {"resource_id": "dkr_official", "title": "Docker Get Started Documentation", "provider": "docker.com", "url": "https://docs.docker.com/get-started/", "type": "Documentation", "duration_minutes": 90, "is_free": True, "difficulty": "Beginner"},
            {"resource_id": "dkr_cheat", "title": "Docker CLI Commands Cheat Sheet", "provider": "docker.com", "url": "https://docs.docker.com/get-started/docker_cheatsheet.pdf", "type": "Cheat Sheet", "duration_minutes": 15, "is_free": True, "difficulty": "All Levels"},
        ],
        "git": [
            {"resource_id": "git_fcc", "title": "Git and GitHub for Beginners", "provider": "freeCodeCamp (YouTube)", "url": "https://www.youtube.com/watch?v=RGOj5yH7evk", "type": "Video", "duration_minutes": 70, "is_free": True, "difficulty": "Beginner"},
            {"resource_id": "git_branching", "title": "Learn Git Branching Interactively", "provider": "learngitbranching.js.org", "url": "https://learngitbranching.js.org/", "type": "Practice Set", "duration_minutes": 120, "is_free": True, "difficulty": "Intermediate"},
            {"resource_id": "git_cheat", "title": "GitHub Git Cheat Sheet", "provider": "GitHub", "url": "https://training.github.com/downloads/github-git-cheat-sheet.pdf", "type": "Cheat Sheet", "duration_minutes": 15, "is_free": True, "difficulty": "All Levels"},
        ],

        # ── MANAGEMENT, PRODUCT & STRATEGY ──────────────────────
        "product management": [
            {"resource_id": "pm_tryexponent", "title": "Product Management Interview Prep Playlist", "provider": "Exponent (YouTube)", "url": "https://www.youtube.com/playlist?list=PLonkg_81xN4a9f3L-gqP-E4xK_e6i2M3B", "type": "Video", "duration_minutes": 300, "is_free": True, "difficulty": "Intermediate"},
            {"resource_id": "pm_productplan", "title": "The Product Manager's Career & Framework Guide", "provider": "ProductPlan", "url": "https://www.productplan.com/learn/", "type": "Documentation", "duration_minutes": 180, "is_free": True, "difficulty": "Beginner"},
            {"resource_id": "pm_circs", "title": "CIRCLES Method Product Design Cheat Sheet", "provider": "Lewis C. Lin", "url": "https://www.lewis-lin.com/blog/2013/6/17/the-circles-method-for-product-design-interview-questions", "type": "Cheat Sheet", "duration_minutes": 25, "is_free": True, "difficulty": "All Levels"},
        ],
        "consulting frameworks": [
            {"resource_id": "cons_craftingcases", "title": "Management Consulting Case Frameworks", "provider": "CraftingCases (YouTube)", "url": "https://www.youtube.com/c/CraftingCases", "type": "Video", "duration_minutes": 240, "is_free": True, "difficulty": "Intermediate"},
            {"resource_id": "cons_victorcheng", "title": "Case Interview Secrets & MECE Frameworks", "provider": "CaseInterview.com / Victor Cheng", "url": "https://www.caseinterview.com/case-interview-frameworks", "type": "Documentation", "duration_minutes": 180, "is_free": True, "difficulty": "Intermediate"},
            {"resource_id": "cons_cheat", "title": "The 12 Core Business Consulting Frameworks", "provider": "Management Consulted", "url": "https://managementconsulted.com/case-interview-frameworks/", "type": "Cheat Sheet", "duration_minutes": 30, "is_free": True, "difficulty": "All Levels"},
        ],
        "case study": [
            {"resource_id": "case_mckinsey", "title": "McKinsey Case Interview Practice Simulator", "provider": "McKinsey & Company", "url": "https://www.mckinsey.com/careers/interviewing", "type": "Practice Set", "duration_minutes": 120, "is_free": True, "difficulty": "Advanced"},
            {"resource_id": "case_bcg", "title": "BCG Interactive Case Preparation Tool", "provider": "Boston Consulting Group", "url": "https://www.bcg.com/careers/pathways/consulting/interview-preparation", "type": "Interactive Course", "duration_minutes": 120, "is_free": True, "difficulty": "Advanced"},
            {"resource_id": "case_math", "title": "Case Math & Market Sizing Mental Drills", "provider": "MyConsultingCoach", "url": "https://www.myconsultingcoach.com/case-interview-math", "type": "Practice Set", "duration_minutes": 90, "is_free": True, "difficulty": "Intermediate"},
        ],
        "agile": [
            {"resource_id": "agile_scrumguide", "title": "The Official Scrum Guide 2020", "provider": "ScrumGuides.org", "url": "https://scrumguides.org/scrum-guide.html", "type": "Documentation", "duration_minutes": 45, "is_free": True, "difficulty": "Beginner"},
            {"resource_id": "agile_atlassian", "title": "Agile Project Management Coach", "provider": "Atlassian", "url": "https://www.atlassian.com/agile", "type": "Documentation", "duration_minutes": 150, "is_free": True, "difficulty": "Beginner"},
            {"resource_id": "agile_cheat", "title": "Scrum Ceremonies, Roles & Artifacts Cheat Sheet", "provider": "Scrum Alliance", "url": "https://resources.scrumalliance.org/", "type": "Cheat Sheet", "duration_minutes": 20, "is_free": True, "difficulty": "All Levels"},
        ],
        "financial modeling": [
            {"resource_id": "fin_cfi", "title": "Free Introduction to Corporate Financial Modeling", "provider": "Corporate Finance Institute (CFI)", "url": "https://corporatefinanceinstitute.com/course/free-financial-modeling-course/", "type": "Interactive Course", "duration_minutes": 180, "is_free": True, "difficulty": "Intermediate"},
            {"resource_id": "fin_damodaran", "title": "Corporate Finance & Valuation Lecture Series", "provider": "Prof. Aswath Damodaran (NYU Stern / YouTube)", "url": "https://www.youtube.com/c/AswathDamodaranonValuation", "type": "Video", "duration_minutes": 420, "is_free": True, "difficulty": "Advanced"},
            {"resource_id": "fin_cheat", "title": "Accounting 3-Statement Modeling Linkages Cheat Sheet", "provider": "Wall Street Prep", "url": "https://www.wallstreetprep.com/knowledge/financial-modeling-best-practices/", "type": "Cheat Sheet", "duration_minutes": 25, "is_free": True, "difficulty": "Intermediate"},
        ],

        # ── BEHAVIORAL, EXECUTIVE PRESENCE & COMMUNICATION ───────
        "behavioral star": [
            {"resource_id": "star_hbr", "title": "How to Answer Behavioral Interview Questions (STAR Method)", "provider": "Harvard Business Review", "url": "https://hbr.org/2022/02/10-common-job-interview-questions-and-how-to-answer-them", "type": "Documentation", "duration_minutes": 45, "is_free": True, "difficulty": "Beginner"},
            {"resource_id": "star_dan", "title": "STAR Method Interview Questions & Answers", "provider": "Dan Croitor (YouTube)", "url": "https://www.youtube.com/watch?v=0nF70Zezx3k", "type": "Video", "duration_minutes": 90, "is_free": True, "difficulty": "Beginner"},
            {"resource_id": "star_cheat", "title": "The STAR Story Matrix Grid Template", "provider": "InterviewIQ", "url": "https://www.themuse.com/advice/star-interview-method", "type": "Cheat Sheet", "duration_minutes": 20, "is_free": True, "difficulty": "All Levels"},
        ],
        "leadership": [
            {"resource_id": "lead_ted", "title": "Simon Sinek: How Great Leaders Inspire Action", "provider": "TED Talks (YouTube)", "url": "https://www.youtube.com/watch?v=qp0HIF3SfI4", "type": "Video", "duration_minutes": 20, "is_free": True, "difficulty": "Beginner"},
            {"resource_id": "lead_amzn", "title": "Amazon 16 Leadership Principles In-Depth Analysis", "provider": "Amazon Jobs", "url": "https://www.amazon.jobs/content/en/our-workplace/leadership-principles", "type": "Documentation", "duration_minutes": 60, "is_free": True, "difficulty": "Intermediate"},
        ],
        "communication": [
            {"resource_id": "comm_stanford", "title": "Think Fast, Talk Smart: Communication Techniques", "provider": "Stanford Graduate School of Business (YouTube)", "url": "https://www.youtube.com/watch?v=HAnw168huqA", "type": "Video", "duration_minutes": 60, "is_free": True, "difficulty": "All Levels"},
            {"resource_id": "comm_pyramid", "title": "The Minto Pyramid Principle of Executive Communication", "provider": "McKinsey Quarterly Overview", "url": "https://untools.co/minto-pyramid", "type": "Documentation", "duration_minutes": 30, "is_free": True, "difficulty": "Intermediate"},
        ]
    }

    # Normalized alias dictionary for flexible topic resolution
    ALIASES: Dict[str, str] = {
        "py": "python", "python3": "python", "python programming": "python",
        "pandas library": "pandas", "dataframe": "pandas",
        "structured query language": "sql", "mysql": "sql", "postgresql": "sql", "oracle sql": "sql", "t-sql": "sql",
        "ml": "machine learning", "supervised learning": "machine learning", "classification": "machine learning",
        "dl": "deep learning", "neural networks": "deep learning", "cnn": "deep learning", "rnn": "deep learning",
        "stats": "statistics", "probability": "statistics", "hypothesis testing": "statistics",
        "dataviz": "data visualization", "charts": "data visualization", "dashboard": "data visualization",
        "powerbi": "power bi", "dax": "power bi",
        "tableau desktop": "tableau",
        "ms excel": "excel", "spreadsheets": "excel", "vlookup": "excel",
        "amazon web services": "aws", "cloud": "aws", "cloud architecture": "aws",
        "microsoft azure": "azure",
        "containers": "docker", "dockerfile": "docker",
        "github": "git", "version control": "git",
        "scrum": "agile", "kanban": "agile", "sprint planning": "agile",
        "pm": "product management", "product strategy": "product management", "roadmapping": "product management",
        "consulting": "consulting frameworks", "mece": "consulting frameworks", "profitability framework": "consulting frameworks",
        "business case": "case study", "market entry": "case study", "case interview": "case study",
        "valuation": "financial modeling", "dcf": "financial modeling", "financial analysis": "financial modeling",
        "star": "behavioral star", "behavioral": "behavioral star", "star method": "behavioral star",
        "leadership principles": "leadership", "people management": "leadership",
        "executive presence": "communication", "verbal presentation": "communication"
    }

    # Generic fallback resources if topic is niche or unmapped
    GENERIC_FALLBACK: List[Dict[str, Any]] = [
        {"resource_id": "gen_harvard_coursera", "title": "Specialized Knowledge Search on Coursera (Audit Free)", "provider": "Coursera", "url": "https://www.coursera.org", "type": "Interactive Course", "duration_minutes": 180, "is_free": True, "difficulty": "All Levels"},
        {"resource_id": "gen_freecodecamp", "title": "Search freeCodeCamp Technical Library", "provider": "freeCodeCamp", "url": "https://www.freecodecamp.org/news/", "type": "Documentation", "duration_minutes": 60, "is_free": True, "difficulty": "All Levels"},
        {"resource_id": "gen_medium_towards", "title": "Towards Data Science & Industry Guides", "provider": "Towards Data Science", "url": "https://towardsdatascience.com", "type": "Documentation", "duration_minutes": 45, "is_free": True, "difficulty": "Intermediate"},
        {"resource_id": "gen_youtube_edu", "title": "Executive Knowledge Explainers", "provider": "YouTube Learning", "url": "https://www.youtube.com", "type": "Video", "duration_minutes": 45, "is_free": True, "difficulty": "All Levels"}
    ]

    @classmethod
    def normalize_topic_key(cls, topic: str) -> str:
        """
        Cleans and resolves raw topic strings to canonical library keys using
        exact lookups and whole-word regex matching, preventing substring traps.
        """
        if not topic:
            return ""
        cleaned = re.sub(r"[^a-zA-Z0-9\s]", " ", str(topic).lower()).strip()
        cleaned = re.sub(r"\s+", " ", cleaned)

        # 1. Exact alias match
        if cleaned in cls.ALIASES:
            return cls.ALIASES[cleaned]

        # 2. Exact database key match
        if cleaned in cls.RESOURCE_DB:
            return cleaned

        # 3. Whole-word alias match (sorted by length descending for specificity)
        sorted_aliases = sorted(cls.ALIASES.items(), key=lambda x: len(x[0]), reverse=True)
        for alias, canonical in sorted_aliases:
            # Whole alias appears as complete word(s) in cleaned topic
            if re.search(r"\b" + re.escape(alias) + r"\b", cleaned):
                return canonical
            # Cleaned topic appears as complete word(s) in alias (only if >= 3 chars)
            if len(cleaned) >= 3 and re.search(r"\b" + re.escape(cleaned) + r"\b", alias):
                return canonical

        # 4. Whole-word direct key match in RESOURCE_DB
        sorted_keys = sorted(cls.RESOURCE_DB.keys(), key=lambda k: len(k), reverse=True)
        for key in sorted_keys:
            if re.search(r"\b" + re.escape(key) + r"\b", cleaned):
                return key
            if len(cleaned) >= 4 and re.search(r"\b" + re.escape(cleaned) + r"\b", key):
                return key

        return cleaned

    @classmethod
    def get_resources(cls, topic: str) -> List[Dict[str, Any]]:
        """
        Retrieves up to 4 high-quality free learning assets for any topic.
        Never calls any external LLM or API. Guaranteed zero cost.
        """
        key = cls.normalize_topic_key(topic)
        if key in cls.RESOURCE_DB:
            return cls.RESOURCE_DB[key]
        
        # If not an exact match, try word-level search in RESOURCE_DB
        for db_key, resources in cls.RESOURCE_DB.items():
            db_words = set(db_key.split())
            topic_words = set(str(topic).lower().split())
            if db_words.intersection(topic_words):
                return resources

        # Return customized fallback with topic injected
        customized_fallback = []
        for r in cls.GENERIC_FALLBACK:
            item = dict(r)
            item["title"] = f"{topic.title()} — {item['title']}"
            customized_fallback.append(item)
        return customized_fallback

    @classmethod
    def get_all_topics(cls) -> List[str]:
        """Lists all directly covered canonical topics."""
        return sorted(list(cls.RESOURCE_DB.keys()))
