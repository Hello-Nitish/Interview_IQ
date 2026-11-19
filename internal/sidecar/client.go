package sidecar

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"time"
)

// Client provides authenticated HTTP methods to communicate with the Python DirectML sidecar.
type Client struct {
	baseURL    string
	token      string
	httpClient *http.Client
}

// NewClient initializes a new sidecar API client.
func NewClient(baseURL, token string) *Client {
	return &Client{
		baseURL: baseURL,
		token:   token,
		httpClient: &http.Client{
			Timeout: 120 * time.Second,
		},
	}
}

func (c *Client) request(method, path string, body interface{}) (map[string]interface{}, error) {
	var bodyReader io.Reader
	if body != nil {
		jsonBytes, err := json.Marshal(body)
		if err != nil {
			return nil, fmt.Errorf("failed to encode request json: %w", err)
		}
		bodyReader = bytes.NewReader(jsonBytes)
	}

	url := fmt.Sprintf("%s%s", c.baseURL, path)
	req, err := http.NewRequest(method, url, bodyReader)
	if err != nil {
		return nil, fmt.Errorf("failed to create http request: %w", err)
	}

	req.Header.Set("Content-Type", "application/json")
	if c.token != "" {
		req.Header.Set("Authorization", fmt.Sprintf("Bearer %s", c.token))
	}

	resp, err := c.httpClient.Do(req)
	if err != nil {
		return nil, fmt.Errorf("sidecar request failed [%s %s]: %w", method, path, err)
	}
	defer resp.Body.Close()

	respBytes, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("failed to read sidecar response body: %w", err)
	}

	var resData map[string]interface{}
	if len(respBytes) > 0 {
		if err := json.Unmarshal(respBytes, &resData); err != nil {
			return nil, fmt.Errorf("invalid json from sidecar (%d): %s", resp.StatusCode, string(respBytes))
		}
	} else {
		resData = make(map[string]interface{})
	}

	if resp.StatusCode >= 400 {
		errMsg := "sidecar error"
		if errVal, ok := resData["error"]; ok {
			errMsg = fmt.Sprintf("%v", errVal)
		} else if msgVal, ok := resData["message"]; ok {
			errMsg = fmt.Sprintf("%v", msgVal)
		}
		return nil, fmt.Errorf("sidecar returned HTTP %d: %s", resp.StatusCode, errMsg)
	}

	return resData, nil
}

func (c *Client) GetHealth() (map[string]interface{}, error) {
	return c.request("GET", "/health", nil)
}

func (c *Client) ValidateAPIKey(apiKey string) (map[string]interface{}, error) {
	return c.request("POST", "/api/auth/validate-key", map[string]interface{}{
		"api_key": apiKey,
	})
}

func (c *Client) GetTelemetry() (map[string]interface{}, error) {
	return c.request("GET", "/api/telemetry", nil)
}

func (c *Client) RunOnboarding(resumeText, jdText, apiKey string) (map[string]interface{}, error) {
	return c.request("POST", "/api/pipeline/onboard", map[string]interface{}{
		"resume_text": resumeText,
		"jd_text":     jdText,
		"api_key":     apiKey,
	})
}

func (c *Client) RunFitAnalysis(profile, jdAnalysis map[string]interface{}) (map[string]interface{}, error) {
	return c.request("POST", "/api/pipeline/fit-analysis", map[string]interface{}{
		"profile":     profile,
		"jd_analysis": jdAnalysis,
	})
}

func (c *Client) GenerateQuestionBank(jdAnalysis, profile, fitReport map[string]interface{}) (map[string]interface{}, error) {
	return c.request("POST", "/api/pipeline/question-bank", map[string]interface{}{
		"jd_analysis": jdAnalysis,
		"profile":     profile,
		"fit_report":  fitReport,
	})
}

func (c *Client) GenerateOnlineTest(qb, jdAnalysis map[string]interface{}) (map[string]interface{}, error) {
	return c.request("POST", "/api/pipeline/online-test", map[string]interface{}{
		"question_bank": qb,
		"jd_analysis":   jdAnalysis,
	})
}

func (c *Client) ScoreOnlineTest(testQuestions []interface{}, userAnswers map[string]interface{}) (map[string]interface{}, error) {
	return c.request("POST", "/api/pipeline/score-test", map[string]interface{}{
		"test_questions": testQuestions,
		"user_answers":   userAnswers,
	})
}

func (c *Client) GenerateFeedback(fitReport, testResults map[string]interface{}, candidateName string) (map[string]interface{}, error) {
	return c.request("POST", "/api/pipeline/feedback", map[string]interface{}{
		"fit_report":     fitReport,
		"test_results":   testResults,
		"candidate_name": candidateName,
	})
}

func (c *Client) GenerateCurriculum(feedback, jdAnalysis map[string]interface{}) (map[string]interface{}, error) {
	return c.request("POST", "/api/pipeline/curriculum", map[string]interface{}{
		"feedback":    feedback,
		"jd_analysis": jdAnalysis,
	})
}

func (c *Client) ToggleCurriculumTask(sessionID string, dayNumber int, taskID string, completed bool) (map[string]interface{}, error) {
	return c.request("POST", "/api/curriculum/toggle-task", map[string]interface{}{
		"session_id": sessionID,
		"day_number": dayNumber,
		"task_id":    taskID,
		"completed":  completed,
	})
}

func (c *Client) TranscribeAudio(audioBase64 string) (map[string]interface{}, error) {
	return c.request("POST", "/api/voice/transcribe", map[string]interface{}{
		"audio_base64": audioBase64,
	})
}

func (c *Client) SemanticSimilarity(query string, candidates []string) (map[string]interface{}, error) {
	return c.request("POST", "/api/semantic/similarity", map[string]interface{}{
		"query":      query,
		"candidates": candidates,
	})
}

func (c *Client) ExportPDF(docType string, fitReport map[string]interface{}, candidateName, roleTitle string) (map[string]interface{}, error) {
	return c.request("POST", "/api/export/pdf", map[string]interface{}{
		"type":           docType,
		"fit_report":     fitReport,
		"candidate_name": candidateName,
		"role_title":     roleTitle,
	})
}

func (c *Client) ListSessions() (map[string]interface{}, error) {
	return c.request("GET", "/api/sessions", nil)
}

func (c *Client) LoadSession(sessionID string) (map[string]interface{}, error) {
	return c.request("GET", fmt.Sprintf("/api/sessions/%s", sessionID), nil)
}
