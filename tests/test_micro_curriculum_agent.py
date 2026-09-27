"""
tests/test_micro_curriculum_agent.py
Unit tests for Phase 25C: Dynamic 7-Day Personalized Micro-Curriculum & Resource Library.
"""

import unittest
from agents.micro_curriculum_agent import MicroCurriculumAgent
from utils.curriculum_resources import CurriculumResourceLibrary
from utils.database import DatabaseManager

class TestMicroCurriculumAgent(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        DatabaseManager.init_db()
        cls.agent = MicroCurriculumAgent()

    def test_generate_curriculum_returns_7_days(self):
        """Validates generate_curriculum returns exactly 7 days of structured preparation."""
        weak_topics = [
            {"topic": "SQL Queries", "priority": "High Priority", "is_dual_weakness": True},
            {"topic": "Python Pandas", "priority": "High Priority"},
            {"topic": "AWS Cloud", "priority": "Medium Priority"}
        ]
        jd = {"role_title": "Data & Product Analyst", "company_name": "Amazon"}
        plan = self.agent.generate_curriculum(weak_topics, jd, composite_score=68.0)
        
        self.assertIn("plan_title", plan)
        self.assertIn("days", plan)
        self.assertEqual(len(plan["days"]), 7)
        self.assertIn("emergency_sprint", plan)

    def test_all_days_have_required_keys(self):
        """Validates each day object contains complete milestones and curated resources."""
        plan = self.agent.generate_curriculum()
        for day in plan["days"]:
            self.assertIn("day_number", day)
            self.assertIn("theme", day)
            self.assertIn("focus_topics", day)
            self.assertIn("learning_objective", day)
            self.assertIn("time_allocation_hours", day)
            self.assertIn("activities", day)
            self.assertIn("milestone_checkpoint", day)
            self.assertIn("resources", day)
            self.assertIsInstance(day["resources"], list)
            self.assertGreater(len(day["resources"]), 0)

    def test_high_priority_topics_assigned_to_day_1_3(self):
        """Validates that high priority topics are prioritized in Days 1 to 3."""
        weak = [
            {"topic": "SQL Optimization", "priority": "High Priority", "is_dual_weakness": True},
            {"topic": "Scrum Ceremonies", "priority": "Low Priority"}
        ]
        plan = self.agent.generate_curriculum(weak_topics=weak)
        day1_topics = [t.lower() for t in plan["days"][0].get("focus_topics", [])]
        self.assertTrue(any("sql" in t for t in day1_topics) or "sql" in plan["days"][0]["theme"].lower())

    def test_curriculum_resource_library_maps_common_topics(self):
        """Validates CurriculumResourceLibrary retrieves curated assets for key topics."""
        py_res = CurriculumResourceLibrary.get_resources("Python")
        self.assertGreater(len(py_res), 0)
        self.assertTrue(any("python" in r["title"].lower() for r in py_res))

        sql_res = CurriculumResourceLibrary.get_resources("SQL")
        self.assertGreater(len(sql_res), 0)
        self.assertTrue(any("sql" in r["title"].lower() for r in sql_res))

        aws_res = CurriculumResourceLibrary.get_resources("AWS")
        self.assertGreater(len(aws_res), 0)

    def test_resource_library_returns_free_resources(self):
        """Validates all curated resources in library are flagged as 100% free (zero cost)."""
        topics = ["Python", "SQL", "Pandas", "Agile", "Excel"]
        for t in topics:
            res_list = CurriculumResourceLibrary.get_resources(t)
            for r in res_list:
                self.assertTrue(r.get("is_free", False))
                self.assertTrue(r["url"].startswith("http"))
                self.assertIn(r["type"], ["Video", "Interactive Course", "Documentation", "Practice Set", "Cheat Sheet"])

    def test_emergency_sprint_returns_2_days(self):
        """Validates emergency 2-day sprint plan is generated for short timelines."""
        plan = self.agent.generate_curriculum()
        sprint = plan.get("emergency_sprint", {})
        self.assertIn("day_1", sprint)
        self.assertIn("day_2", sprint)
        self.assertIn("core_actions", sprint["day_1"])
        self.assertIn("core_actions", sprint["day_2"])

    def test_db_save_and_retrieve_curriculum(self):
        """Validates SQLite persistence of 7-day curriculum plan."""
        user_id = DatabaseManager.get_or_create_user("Curriculum Test Candidate")
        sess_id = DatabaseManager.create_session(user_id, "Curriculum Test Candidate", "Product Manager")
        
        plan_dict = {"plan_title": "Test 7-Day Plan", "days": []}
        plan_id = DatabaseManager.save_curriculum_plan(sess_id, plan_dict)
        self.assertTrue(plan_id.startswith("plan_"))
        
        saved = DatabaseManager.get_curriculum_plan(sess_id)
        self.assertIsNotNone(saved)
        self.assertEqual(saved["plan_id"], plan_id)
        self.assertEqual(saved["plan"]["plan_title"], "Test 7-Day Plan")

    def test_db_update_progress_tracking(self):
        """Validates updating checklist progress in SQLite."""
        user_id = DatabaseManager.get_or_create_user("Progress Test Candidate")
        sess_id = DatabaseManager.create_session(user_id, "Progress Test Candidate", "Product Manager")
        
        plan_dict = {"plan_title": "Progress Plan", "days": []}
        plan_id = DatabaseManager.save_curriculum_plan(sess_id, plan_dict)
        
        checked = ["py_yt_full", "sql_mosh"]
        DatabaseManager.update_curriculum_progress(plan_id, checked, days_completed=2)
        
        updated = DatabaseManager.get_curriculum_plan(sess_id)
        self.assertEqual(updated["checked_items_list"], checked)
        self.assertEqual(updated["days_completed"], 2)

    def test_topic_normalization_edge_cases(self):
        """Validates that short topics like 'a' or 'it' do not falsely match substrings."""
        # Short strings should not falsely map to python or statistics
        self.assertEqual(CurriculumResourceLibrary.normalize_topic_key("a"), "a")
        self.assertEqual(CurriculumResourceLibrary.normalize_topic_key("it"), "it")

        # Canonical aliases should resolve
        self.assertEqual(CurriculumResourceLibrary.normalize_topic_key("SQL & Relational DB"), "sql")
        self.assertEqual(CurriculumResourceLibrary.normalize_topic_key("Python programming"), "python")
        self.assertEqual(CurriculumResourceLibrary.normalize_topic_key("AWS Cloud"), "aws")
        self.assertEqual(CurriculumResourceLibrary.normalize_topic_key("PM"), "product management")

        # Empty string handling
        self.assertEqual(CurriculumResourceLibrary.normalize_topic_key(""), "")

if __name__ == "__main__":
    unittest.main()
