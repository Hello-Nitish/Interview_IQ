"""
Unit Tests for Desktop Architecture (Go + Wails v2 + React 18 + TS + Tailwind + Python DirectML Sidecar).
Validates configuration files, Go source structure, frontend component contracts, and launcher integrity.
"""

import json
import os
import unittest

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class TestDesktopWailsStack(unittest.TestCase):
    """Verifies that all files and contracts for the native desktop stack are in place."""

    def test_wails_json_configuration(self):
        """Verify wails.json exists and contains correct application metadata."""
        wails_path = os.path.join(project_root, "wails.json")
        self.assertTrue(os.path.exists(wails_path), "wails.json must exist in project root")

        with open(wails_path, "r", encoding="utf-8") as f:
            config = json.load(f)

        self.assertEqual(config.get("name"), "InterviewIQ")
        self.assertIn("frontend:build", config)
        self.assertEqual(config["frontend:build"], "npm run build")
        self.assertEqual(config.get("outputfilename"), "InterviewIQ")

    def test_go_source_files_exist_and_valid(self):
        """Verify main.go, app.go, and go.mod are present with required symbols."""
        main_path = os.path.join(project_root, "main.go")
        app_path = os.path.join(project_root, "app.go")
        mod_path = os.path.join(project_root, "go.mod")

        self.assertTrue(os.path.exists(main_path), "main.go must exist")
        self.assertTrue(os.path.exists(app_path), "app.go must exist")
        self.assertTrue(os.path.exists(mod_path), "go.mod must exist")

        with open(main_path, "r", encoding="utf-8") as f:
            main_code = f.read()
        self.assertIn("package main", main_code)
        self.assertIn("go:embed all:frontend/dist", main_code)
        self.assertIn("wails.Run", main_code)

        with open(app_path, "r", encoding="utf-8") as f:
            app_code = f.read()
        self.assertIn("type App struct", app_code)
        self.assertIn("sidecarManager", app_code)
        self.assertIn("SelectResumeFile", app_code)
        self.assertIn("RunOnboarding", app_code)
        self.assertIn("ExportPDF", app_code)

    def test_sidecar_go_supervisor_and_client(self):
        """Verify internal/sidecar manager.go and client.go exist."""
        manager_path = os.path.join(project_root, "internal", "sidecar", "manager.go")
        client_path = os.path.join(project_root, "internal", "sidecar", "client.go")

        self.assertTrue(os.path.exists(manager_path), "manager.go must exist")
        self.assertTrue(os.path.exists(client_path), "client.go must exist")

        with open(manager_path, "r", encoding="utf-8") as f:
            mgr_code = f.read()
        self.assertIn("type Manager struct", mgr_code)
        self.assertIn("generateSecureToken", mgr_code)
        self.assertIn("sidecar.server", mgr_code)

    def test_frontend_react_files_exist(self):
        """Verify frontend React/TypeScript/Tailwind configuration and core pages."""
        frontend_dir = os.path.join(project_root, "frontend")
        pkg_path = os.path.join(frontend_dir, "package.json")
        tailwind_path = os.path.join(frontend_dir, "tailwind.config.js")
        app_tsx = os.path.join(frontend_dir, "src", "App.tsx")

        self.assertTrue(os.path.exists(pkg_path), "package.json must exist")
        self.assertTrue(os.path.exists(tailwind_path), "tailwind.config.js must exist")
        self.assertTrue(os.path.exists(app_tsx), "App.tsx must exist")

        # Verify all 6 pages exist
        pages = [
            "Step1Upload.tsx",
            "Step2FitReport.tsx",
            "Step3QuestionBank.tsx",
            "Step4OnlineTest.tsx",
            "Step5Results.tsx",
            "Step6Curriculum.tsx",
        ]
        for page_name in pages:
            page_path = os.path.join(frontend_dir, "src", "pages", page_name)
            self.assertTrue(os.path.exists(page_path), f"Page {page_name} must exist")

        # Verify key components exist
        components = [
            "Header.tsx",
            "Sidebar.tsx",
            "Stepper.tsx",
            "MetricCard.tsx",
            "Badge.tsx",
            "AudioRecorder.tsx",
            "ExamTimer.tsx",
        ]
        for comp_name in components:
            comp_path = os.path.join(frontend_dir, "src", "components", comp_name)
            self.assertTrue(os.path.exists(comp_path), f"Component {comp_name} must exist")

    def test_direct_launch_batch_file_exists(self):
        """Verify launch.bat exists and contains automated sidecar launch and UI opening."""
        bat_path = os.path.join(project_root, "launch.bat")
        self.assertTrue(os.path.exists(bat_path), "launch.bat must exist in project root")

        with open(bat_path, "r", encoding="utf-8") as f:
            bat_code = f.read()
        self.assertIn("sidecar.server", bat_code)
        self.assertIn("http://127.0.0.1:8000", bat_code)


if __name__ == "__main__":
    unittest.main()
