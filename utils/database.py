import os
import sqlite3
import json
from datetime import datetime
from typing import Optional, List, Dict, Any

class DatabaseManager:
    """
    SQLite Relational Persistence Layer for InterviewIQ.
    Persists candidate profiles, assessment sessions, test attempts,
    and multi-round diagnostic reports for longitudinal tracking.
    """
    DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'interviewiq.db')
    _initialized_paths: set = set()

    @classmethod
    def get_connection(cls) -> sqlite3.Connection:
        os.makedirs(os.path.dirname(cls.DB_PATH), exist_ok=True)
        conn = sqlite3.connect(cls.DB_PATH, timeout=10.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA synchronous = NORMAL;")
        conn.execute("PRAGMA cache_size = -64000;")
        conn.execute("PRAGMA temp_store = MEMORY;")
        conn.execute("PRAGMA mmap_size = 268435456;")
        return conn

    @classmethod
    def init_db(cls, force: bool = False):
        """Initializes relational tables if they do not exist."""
        path = os.path.abspath(cls.DB_PATH)
        if path in cls._initialized_paths and not force:
            return
        with cls.get_connection() as conn:
            cursor = conn.cursor()
            
            # 1. Users / Candidates
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                full_name TEXT NOT NULL,
                email TEXT,
                target_domain TEXT,
                created_at TEXT NOT NULL
            );
            """)

            # 2. Sessions
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                user_id TEXT,
                candidate_name TEXT NOT NULL,
                role_title TEXT,
                current_round INTEGER DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE SET NULL
            );
            """)

            # 3. Fit Evaluations
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS fit_evaluations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                technical_match_pct REAL,
                experience_score INTEGER,
                decision TEXT,
                rule_triggered TEXT,
                requirements_matrix_json TEXT,
                full_fit_json TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
            );
            """)

            # 4. Test Attempts (Scored 30-MCQs per round)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS test_attempts (
                attempt_id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                round_number INTEGER NOT NULL,
                score INTEGER NOT NULL,
                total_questions INTEGER NOT NULL,
                percentage REAL NOT NULL,
                passed INTEGER NOT NULL,
                topic_accuracy_json TEXT,
                answers_json TEXT,
                test_data_json TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
            );
            """)

            # 5. Readiness & Diagnostic Reports
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS readiness_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                round_number INTEGER NOT NULL,
                composite_score REAL,
                readiness_level TEXT,
                unified_matrix_json TEXT,
                study_roadmap_json TEXT,
                prioritized_topics_json TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
            );
            """)

            # 6. Full Session State Snapshots (for seamless state restoration)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS session_snapshots (
                session_id TEXT PRIMARY KEY,
                state_json TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
            );
            """)

            # 7. Two-Tier Response Cache for Gemini API Quota Optimization
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS api_response_cache (
                prompt_hash TEXT PRIMARY KEY,
                model_name TEXT NOT NULL,
                is_json INTEGER NOT NULL,
                response_text TEXT NOT NULL,
                created_at TEXT NOT NULL,
                hit_count INTEGER DEFAULT 1
            );
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_cache_created ON api_response_cache(created_at);")

            # 8. Dynamic 7-Day Micro-Curriculum Plans
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS curriculum_plans (
                plan_id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                plan_json TEXT NOT NULL,
                checked_items TEXT,
                days_completed INTEGER DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
            );
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_created ON sessions(created_at);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_fit_session ON fit_evaluations(session_id);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_test_session ON test_attempts(session_id);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_test_round ON test_attempts(session_id, round_number);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_readiness_session ON readiness_reports(session_id);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_readiness_round ON readiness_reports(session_id, round_number);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_curr_session ON curriculum_plans(session_id);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_curr_session_updated ON curriculum_plans(session_id, updated_at);")

            conn.commit()
        cls._initialized_paths.add(path)

    # --- User Management ---

    @classmethod
    def get_or_create_user(cls, full_name: str, email: Optional[str] = None, target_domain: Optional[str] = None) -> str:
        """Finds or creates a user by name/email, returning user_id."""
        cls.init_db()
        full_name = full_name.strip() if full_name else "Candidate"
        with cls.get_connection() as conn:
            cursor = conn.cursor()
            if email:
                cursor.execute("SELECT user_id FROM users WHERE email = ?", (email,))
            else:
                cursor.execute("SELECT user_id FROM users WHERE full_name = ?", (full_name,))
            row = cursor.fetchone()
            if row:
                return row["user_id"]
            
            user_id = "usr_" + datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:19]
            now = datetime.now().isoformat()
            cursor.execute(
                "INSERT INTO users (user_id, full_name, email, target_domain, created_at) VALUES (?, ?, ?, ?, ?)",
                (user_id, full_name, email or "", target_domain or "", now)
            )
            conn.commit()
            return user_id

    @classmethod
    def list_users(cls) -> List[Dict[str, Any]]:
        cls.init_db()
        with cls.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users ORDER BY created_at DESC")
            return [dict(row) for row in cursor.fetchall()]

    # --- Session Management ---

    @classmethod
    def create_session(cls, user_id: str, candidate_name: str = "Candidate", role_title: str = "Role Evaluation") -> str:
        """Explicitly creates a new session record and returns session_id."""
        cls.init_db()
        import uuid
        session_id = f"sess_{uuid.uuid4().hex[:12]}"
        now = datetime.now().isoformat()
        with cls.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO sessions (session_id, user_id, candidate_name, role_title, current_round, created_at, updated_at)
            VALUES (?, ?, ?, ?, 1, ?, ?)
            """, (session_id, user_id, candidate_name, role_title, now, now))
            conn.commit()
        return session_id

    @classmethod
    def save_session_state(cls, session_id: str, state: dict, user_id: Optional[str] = None):
        """Saves full session state and extracts structured relational records."""
        cls.init_db()
        now = datetime.now().isoformat()
        candidate_name = state.get("candidate_name") or (state.get("resume_data") or {}).get("candidate_name") or "Candidate"
        role_title = (state.get("jd_data") or {}).get("role_title") or (state.get("jd_profile") or {}).get("role_title") or "Candidate Evaluation"
        current_round = state.get("round_number") or state.get("round", 1)

        if not user_id:
            user_id = cls.get_or_create_user(candidate_name)

        with cls.get_connection() as conn:
            cursor = conn.cursor()

            # Upsert into sessions
            cursor.execute("""
            INSERT INTO sessions (session_id, user_id, candidate_name, role_title, current_round, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(session_id) DO UPDATE SET
                candidate_name=excluded.candidate_name,
                role_title=excluded.role_title,
                current_round=excluded.current_round,
                updated_at=excluded.updated_at
            """, (session_id, user_id, candidate_name, role_title, current_round, state.get("created_at", now), now))

            # Upsert snapshot
            cursor.execute("""
            INSERT INTO session_snapshots (session_id, state_json, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(session_id) DO UPDATE SET
                state_json=excluded.state_json,
                updated_at=excluded.updated_at
            """, (session_id, json.dumps(state), now))

            # If fit_data exists, record fit evaluation
            fit_data = state.get("fit_data")
            if fit_data and isinstance(fit_data, dict):
                tech_match = fit_data.get("technical_rating", {}).get("technical_match_pct", 0)
                if not tech_match:
                    tech_match = fit_data.get("technical_match_pct", 0)
                exp_score = fit_data.get("experience_scoring", {}).get("awarded_points", 0)
                decision = fit_data.get("decision_engine", {}).get("final_decision", "")
                rule = fit_data.get("decision_engine", {}).get("governing_rule_triggered", "")
                req_matrix = fit_data.get("requirements_matrix", [])

                cursor.execute("SELECT id FROM fit_evaluations WHERE session_id = ?", (session_id,))
                existing = cursor.fetchone()
                if not existing:
                    cursor.execute("""
                    INSERT INTO fit_evaluations (session_id, technical_match_pct, experience_score, decision, rule_triggered, requirements_matrix_json, full_fit_json, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (session_id, float(tech_match or 0), int(exp_score or 0), decision, rule, json.dumps(req_matrix), json.dumps(fit_data), now))

            conn.commit()

    @classmethod
    def load_session_state(cls, session_id: str) -> Optional[dict]:
        """Loads state from SQLite session_snapshots."""
        cls.init_db()
        with cls.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT state_json FROM session_snapshots WHERE session_id = ?", (session_id,))
            row = cursor.fetchone()
            if row:
                return json.loads(row["state_json"])
        return None

    @classmethod
    def list_sessions(cls, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Lists sessions with metadata and latest scores."""
        cls.init_db()
        with cls.get_connection() as conn:
            cursor = conn.cursor()
            if user_id:
                cursor.execute("""
                SELECT s.*, 
                       (SELECT score FROM test_attempts WHERE session_id = s.session_id ORDER BY attempt_id DESC LIMIT 1) as latest_score,
                       (SELECT percentage FROM test_attempts WHERE session_id = s.session_id ORDER BY attempt_id DESC LIMIT 1) as latest_percentage
                FROM sessions s WHERE s.user_id = ? ORDER BY s.updated_at DESC
                """, (user_id,))
            else:
                cursor.execute("""
                SELECT s.*, 
                       (SELECT score FROM test_attempts WHERE session_id = s.session_id ORDER BY attempt_id DESC LIMIT 1) as latest_score,
                       (SELECT percentage FROM test_attempts WHERE session_id = s.session_id ORDER BY attempt_id DESC LIMIT 1) as latest_percentage
                FROM sessions s ORDER BY s.updated_at DESC
                """)
            return [dict(row) for row in cursor.fetchall()]

    # --- Test Attempt Recording ---

    @classmethod
    def record_test_attempt(cls, session_id: str, round_number: int, test_data: dict, results: dict, answers: Optional[dict] = None) -> int:
        """Records a completed 30-MCQ test attempt with detailed scoring."""
        cls.init_db()
        now = datetime.now().isoformat()
        score = results.get("score", 0)
        total_q = results.get("total_questions", 30)
        percentage = results.get("percentage", 0.0)
        passed = 1 if results.get("passed", False) else 0
        topic_acc = json.dumps(results.get("topic_accuracy", {}))
        answers_str = json.dumps(answers or {})
        test_str = json.dumps(test_data or {})

        with cls.get_connection() as conn:
            cursor = conn.cursor()
            # Ensure session row exists to satisfy foreign key
            cursor.execute("""
            INSERT INTO sessions (session_id, user_id, candidate_name, role_title, current_round, created_at, updated_at)
            VALUES (?, NULL, 'Candidate', 'Evaluation', ?, ?, ?)
            ON CONFLICT(session_id) DO UPDATE SET current_round = excluded.current_round, updated_at = excluded.updated_at
            """, (session_id, round_number, now, now))

            cursor.execute("""
            INSERT INTO test_attempts (session_id, round_number, score, total_questions, percentage, passed, topic_accuracy_json, answers_json, test_data_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (session_id, round_number, score, total_q, percentage, passed, topic_acc, answers_str, test_str, now))
            attempt_id = cursor.lastrowid
            
            conn.commit()
            return attempt_id

    @classmethod
    def get_test_attempts(cls, session_id: str) -> List[Dict[str, Any]]:
        cls.init_db()
        with cls.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM test_attempts WHERE session_id = ? ORDER BY round_number ASC, attempt_id ASC", (session_id,))
            rows = cursor.fetchall()
            results = []
            for r in rows:
                item = dict(r)
                item["topic_accuracy"] = json.loads(item["topic_accuracy_json"]) if item["topic_accuracy_json"] else {}
                item["answers"] = json.loads(item["answers_json"]) if item["answers_json"] else {}
                results.append(item)
            return results

    @classmethod
    def get_round_comparison(cls, session_id: str) -> Dict[str, Any]:
        """Calculates score progression across test rounds (e.g. Round 1 vs Round 2)."""
        attempts = cls.get_test_attempts(session_id)
        if not attempts:
            return {"has_history": False, "attempts": []}
        
        rounds_summary = []
        for att in attempts:
            rounds_summary.append({
                "round": att["round_number"],
                "score": att["score"],
                "total": att["total_questions"],
                "percentage": att["percentage"],
                "passed": bool(att["passed"]),
                "date": att["created_at"]
            })
        
        improvement = 0.0
        if len(rounds_summary) >= 2:
            improvement = round(rounds_summary[-1]["percentage"] - rounds_summary[0]["percentage"], 1)

        return {
            "has_history": len(rounds_summary) > 1,
            "total_rounds": len(rounds_summary),
            "rounds": rounds_summary,
            "net_improvement_pct": improvement
        }

    # --- Readiness & Diagnostic Reports ---

    @classmethod
    def record_readiness_report(cls, session_id: str, round_number: int, feedback: dict):
        cls.init_db()
        now = datetime.now().isoformat()
        comp_score = feedback.get("overall_readiness_score") or feedback.get("composite_readiness_score") or 0.0
        readiness_lvl = feedback.get("readiness_level", "Moderate")
        unified_matrix = json.dumps(feedback.get("unified_topic_readiness", []))
        study_plan = json.dumps(feedback.get("targeted_study_plan_next_48h", []))
        prio_topics = json.dumps(feedback.get("prioritized_topics_for_next_round", []))

        with cls.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO sessions (session_id, user_id, candidate_name, role_title, current_round, created_at, updated_at)
            VALUES (?, NULL, 'Candidate', 'Evaluation', ?, ?, ?)
            ON CONFLICT(session_id) DO UPDATE SET current_round = excluded.current_round, updated_at = excluded.updated_at
            """, (session_id, round_number, now, now))

            cursor.execute("""
            INSERT INTO readiness_reports (session_id, round_number, composite_score, readiness_level, unified_matrix_json, study_roadmap_json, prioritized_topics_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (session_id, round_number, float(comp_score or 0), readiness_lvl, unified_matrix, study_plan, prio_topics, now))
            conn.commit()

    @classmethod
    def get_latest_readiness_report(cls, session_id: str) -> Optional[Dict[str, Any]]:
        cls.init_db()
        with cls.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM readiness_reports WHERE session_id = ? ORDER BY id DESC LIMIT 1", (session_id,))
            row = cursor.fetchone()
            if row:
                res = dict(row)
                res["unified_matrix"] = json.loads(res["unified_matrix_json"]) if res["unified_matrix_json"] else []
                res["study_roadmap"] = json.loads(res["study_roadmap_json"]) if res["study_roadmap_json"] else []
                res["prioritized_topics"] = json.loads(res["prioritized_topics_json"]) if res["prioritized_topics_json"] else []
                return res
        return None

    # --- API Response Cache (L2 Cache) ---

    @classmethod
    def get_api_cache_entry(cls, prompt_hash: str) -> Optional[str]:
        """Retrieves cached response from SQLite by SHA-256 prompt hash, incrementing hit count."""
        cls.init_db()
        with cls.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT response_text FROM api_response_cache WHERE prompt_hash = ?", (prompt_hash,))
            row = cursor.fetchone()
            if row:
                cursor.execute("UPDATE api_response_cache SET hit_count = hit_count + 1 WHERE prompt_hash = ?", (prompt_hash,))
                conn.commit()
                return row["response_text"]
        return None

    @classmethod
    def save_api_cache_entry(cls, prompt_hash: str, model_name: str, is_json: bool, response_text: str):
        """Persists prompt-response pair into SQLite cache."""
        cls.init_db()
        now = datetime.now().isoformat()
        with cls.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO api_response_cache (prompt_hash, model_name, is_json, response_text, created_at, hit_count)
            VALUES (?, ?, ?, ?, ?, 1)
            ON CONFLICT(prompt_hash) DO UPDATE SET
                response_text = excluded.response_text,
                hit_count = hit_count + 1
            """, (prompt_hash, model_name, 1 if is_json else 0, response_text, now))
            conn.commit()

    @classmethod
    def clear_api_cache(cls):
        """Clears all cached API responses from SQLite."""
        cls.init_db()
        with cls.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM api_response_cache;")
            conn.commit()

    # --- 7-Day Micro-Curriculum Persistence ---

    @classmethod
    def save_curriculum_plan(
        cls,
        session_id: str,
        plan_dict: Dict[str, Any]
    ) -> str:
        """Persists or replaces a 7-day personalized micro-curriculum plan."""
        cls.init_db()
        import uuid
        plan_id = f"plan_{uuid.uuid4().hex[:10]}"
        now = datetime.now().isoformat()
        plan_json = json.dumps(plan_dict)

        with cls.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO sessions (session_id, user_id, candidate_name, role_title, current_round, created_at, updated_at)
            VALUES (?, NULL, 'Candidate', 'Evaluation', 1, ?, ?)
            ON CONFLICT(session_id) DO NOTHING
            """, (session_id, now, now))
            # Remove any older plan for this session to ensure 1 active latest plan
            cursor.execute("DELETE FROM curriculum_plans WHERE session_id = ?", (session_id,))
            cursor.execute("""
            INSERT INTO curriculum_plans (plan_id, session_id, plan_json, checked_items, days_completed, created_at, updated_at)
            VALUES (?, ?, ?, ?, 0, ?, ?)
            """, (plan_id, session_id, plan_json, json.dumps([]), now, now))
            conn.commit()
        return plan_id

    @classmethod
    def get_curriculum_plan(cls, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves active curriculum plan and checklist state for a session."""
        cls.init_db()
        with cls.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM curriculum_plans WHERE session_id = ? ORDER BY updated_at DESC LIMIT 1", (session_id,))
            row = cursor.fetchone()
            if row:
                res = dict(row)
                res["plan"] = json.loads(res["plan_json"]) if res["plan_json"] else {}
                res["checked_items_list"] = json.loads(res["checked_items"]) if res["checked_items"] else []
                return res
            return None

    @classmethod
    def update_curriculum_progress(
        cls,
        plan_id: str,
        checked_items: List[str],
        days_completed: int = 0
    ):
        """Updates progress tracking checkboxes for an active curriculum plan."""
        cls.init_db()
        now = datetime.now().isoformat()
        with cls.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            UPDATE curriculum_plans
            SET checked_items = ?, days_completed = ?, updated_at = ?
            WHERE plan_id = ?
            """, (json.dumps(checked_items), days_completed, now, plan_id))
            conn.commit()


