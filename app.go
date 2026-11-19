package main

import (
	"context"
	"fmt"
	"os"
	"path/filepath"

	"interviewiq/internal/sidecar"

	"github.com/wailsapp/wails/v2/pkg/runtime"
)

// App struct manages desktop state and bindings
type App struct {
	ctx            context.Context
	sidecarManager *sidecar.Manager
}

// NewApp creates a new App application struct
func NewApp() *App {
	return &App{
		sidecarManager: sidecar.NewManager("", 0),
	}
}

// startup is called when the app starts. The context is saved
// so we can call the runtime methods.
func (a *App) startup(ctx context.Context) {
	a.ctx = ctx
	if err := a.sidecarManager.Start(); err != nil {
		runtime.LogErrorf(ctx, "Failed to start Python DirectML sidecar: %s", err)
	}
}

// shutdown is called at application termination
func (a *App) shutdown(ctx context.Context) {
	if a.sidecarManager != nil {
		_ = a.sidecarManager.Stop()
	}
}

// GetStatus returns the health and DirectML hardware status
func (a *App) GetStatus() (map[string]interface{}, error) {
	client := a.sidecarManager.GetClient()
	if client == nil {
		return map[string]interface{}{"status": "sidecar_offline"}, nil
	}
	return client.GetHealth()
}

// SelectResumeFile opens a native OS file dialog for PDF, DOCX, and TXT files
func (a *App) SelectResumeFile() (map[string]interface{}, error) {
	selectedFile, err := runtime.OpenFileDialog(a.ctx, runtime.OpenDialogOptions{
		Title: "Select Candidate Resume",
		Filters: []runtime.FileFilter{
			{
				DisplayName: "Resumes (*.pdf;*.docx;*.txt)",
				Pattern:     "*.pdf;*.docx;*.txt",
			},
			{
				DisplayName: "All Files (*.*)",
				Pattern:     "*.*",
			},
		},
	})
	if err != nil {
		return nil, fmt.Errorf("file dialog error: %w", err)
	}
	if selectedFile == "" {
		return map[string]interface{}{"cancelled": true}, nil
	}

	content := ""
	data, err := os.ReadFile(selectedFile)
	if err == nil {
		content = string(data)
	}

	return map[string]interface{}{
		"cancelled": false,
		"filePath":  selectedFile,
		"fileName":  filepath.Base(selectedFile),
		"content":   content,
		"size":      len(data),
	}, nil
}

// ValidateAPIKey validates Gemini API key
func (a *App) ValidateAPIKey(apiKey string) (map[string]interface{}, error) {
	client := a.sidecarManager.GetClient()
	if client == nil {
		return nil, fmt.Errorf("sidecar client not ready")
	}
	return client.ValidateAPIKey(apiKey)
}

// GetTelemetry retrieves live API quota and DirectML hardware usage
func (a *App) GetTelemetry() (map[string]interface{}, error) {
	client := a.sidecarManager.GetClient()
	if client == nil {
		return nil, fmt.Errorf("sidecar client not ready")
	}
	return client.GetTelemetry()
}

// RunOnboarding runs Step 1 candidate profiling and JD analysis
func (a *App) RunOnboarding(resumeText, jdText, apiKey string) (map[string]interface{}, error) {
	client := a.sidecarManager.GetClient()
	if client == nil {
		return nil, fmt.Errorf("sidecar client not ready")
	}
	return client.RunOnboarding(resumeText, jdText, apiKey)
}

// RunFitAnalysis executes Step 2 Strategic Fit evaluation
func (a *App) RunFitAnalysis(profile, jdAnalysis map[string]interface{}) (map[string]interface{}, error) {
	client := a.sidecarManager.GetClient()
	if client == nil {
		return nil, fmt.Errorf("sidecar client not ready")
	}
	return client.RunFitAnalysis(profile, jdAnalysis)
}

// GenerateQuestionBank generates Step 3 5-dimensional question bank
func (a *App) GenerateQuestionBank(jdAnalysis, profile, fitReport map[string]interface{}) (map[string]interface{}, error) {
	client := a.sidecarManager.GetClient()
	if client == nil {
		return nil, fmt.Errorf("sidecar client not ready")
	}
	return client.GenerateQuestionBank(jdAnalysis, profile, fitReport)
}

// GenerateOnlineTest generates Step 4 30-MCQ examination with anti-cheat shuffle
func (a *App) GenerateOnlineTest(qb, jdAnalysis map[string]interface{}) (map[string]interface{}, error) {
	client := a.sidecarManager.GetClient()
	if client == nil {
		return nil, fmt.Errorf("sidecar client not ready")
	}
	return client.GenerateOnlineTest(qb, jdAnalysis)
}

// ScoreOnlineTest scores candidate answers
func (a *App) ScoreOnlineTest(testQuestions []interface{}, userAnswers map[string]interface{}) (map[string]interface{}, error) {
	client := a.sidecarManager.GetClient()
	if client == nil {
		return nil, fmt.Errorf("sidecar client not ready")
	}
	return client.ScoreOnlineTest(testQuestions, userAnswers)
}

// GenerateFeedback computes Step 5 45/55 composite readiness and 48h roadmap
func (a *App) GenerateFeedback(fitReport, testResults map[string]interface{}, candidateName string) (map[string]interface{}, error) {
	client := a.sidecarManager.GetClient()
	if client == nil {
		return nil, fmt.Errorf("sidecar client not ready")
	}
	return client.GenerateFeedback(fitReport, testResults, candidateName)
}

// GenerateCurriculum builds Step 6 7-day personalized micro-curriculum
func (a *App) GenerateCurriculum(feedback, jdAnalysis map[string]interface{}) (map[string]interface{}, error) {
	client := a.sidecarManager.GetClient()
	if client == nil {
		return nil, fmt.Errorf("sidecar client not ready")
	}
	return client.GenerateCurriculum(feedback, jdAnalysis)
}

// ToggleCurriculumTask updates checklist status in SQLite
func (a *App) ToggleCurriculumTask(sessionID string, dayNumber int, taskID string, completed bool) (map[string]interface{}, error) {
	client := a.sidecarManager.GetClient()
	if client == nil {
		return nil, fmt.Errorf("sidecar client not ready")
	}
	return client.ToggleCurriculumTask(sessionID, dayNumber, taskID, completed)
}

// TranscribeAudio transcribes voice recording via DirectML Whisper
func (a *App) TranscribeAudio(audioBase64 string) (map[string]interface{}, error) {
	client := a.sidecarManager.GetClient()
	if client == nil {
		return nil, fmt.Errorf("sidecar client not ready")
	}
	return client.TranscribeAudio(audioBase64)
}

// ExportPDF exports standalone fit report or full dossier vector PDF
func (a *App) ExportPDF(docType string, fitReport map[string]interface{}, candidateName, roleTitle string) (map[string]interface{}, error) {
	client := a.sidecarManager.GetClient()
	if client == nil {
		return nil, fmt.Errorf("sidecar client not ready")
	}
	return client.ExportPDF(docType, fitReport, candidateName, roleTitle)
}

// ListSessions lists historical sessions from SQLite
func (a *App) ListSessions() (map[string]interface{}, error) {
	client := a.sidecarManager.GetClient()
	if client == nil {
		return nil, fmt.Errorf("sidecar client not ready")
	}
	return client.ListSessions()
}

// LoadSession loads a past session by ID
func (a *App) LoadSession(sessionID string) (map[string]interface{}, error) {
	client := a.sidecarManager.GetClient()
	if client == nil {
		return nil, fmt.Errorf("sidecar client not ready")
	}
	return client.LoadSession(sessionID)
}
