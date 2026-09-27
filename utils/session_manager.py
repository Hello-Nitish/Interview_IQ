import json, os
from datetime import datetime

class SessionManager:
    SESSIONS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'sessions')

    @classmethod
    def create_session(cls, candidate_name: str = 'Candidate') -> str:
        os.makedirs(cls.SESSIONS_DIR, exist_ok=True)
        session_id = 'session_' + datetime.now().strftime('%Y%m%d_%H%M%S_%f')
        initial_state = {
            'session_id': session_id,
            'created_at': datetime.now().isoformat(),
            'candidate_name': candidate_name,
            'resume_data': None,
            'jd_data': None,
            'fit_data': None,
            'question_bank': None,
            'transcript': [],
            'evaluation': None,
            'feedback': None
        }
        cls.save_session(session_id, initial_state)
        return session_id

    @classmethod
    def save_session(cls, session_id: str, state: dict):
        os.makedirs(cls.SESSIONS_DIR, exist_ok=True)
        file_path = os.path.join(cls.SESSIONS_DIR, session_id + '.json')
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(state, f, indent=2)
        try:
            from utils.database import DatabaseManager
            DatabaseManager.save_session_state(session_id, state)
        except Exception:
            pass

    @classmethod
    def load_session(cls, session_id: str) -> dict:
        file_path = os.path.join(cls.SESSIONS_DIR, session_id + '.json')
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        try:
            from utils.database import DatabaseManager
            db_state = DatabaseManager.load_session_state(session_id)
            if db_state:
                return db_state
        except Exception:
            pass
        raise FileNotFoundError('Session ' + session_id + ' not found.')