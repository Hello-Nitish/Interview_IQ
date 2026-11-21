import * as WailsApp from '../wailsjs/go/main/App';

const SIDECAR_HTTP_URL = typeof window !== 'undefined' && window.location?.origin?.startsWith('http') 
  ? window.location.origin 
  : 'http://127.0.0.1:8000';

function isWailsAvailable(): boolean {
  return typeof window !== 'undefined' && (window as any).go?.main?.App !== undefined;
}

async function httpFallback(endpoint: string, method: string = 'GET', body?: any): Promise<any> {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  const res = await fetch(`${SIDECAR_HTTP_URL}${endpoint}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData.error || errData.message || `HTTP ${res.status}`);
  }
  return res.json();
}

export const API = {
  getStatus: async () => {
    if (isWailsAvailable()) {
      return WailsApp.GetStatus();
    }
    return httpFallback('/health', 'GET');
  },

  validateApiKey: async (apiKey: string) => {
    if (isWailsAvailable()) {
      return WailsApp.ValidateAPIKey(apiKey);
    }
    return httpFallback('/api/auth/validate-key', 'POST', { api_key: apiKey });
  },

  getTelemetry: async () => {
    if (isWailsAvailable()) {
      return WailsApp.GetTelemetry();
    }
    return httpFallback('/api/telemetry', 'GET');
  },

  selectResumeFile: async () => {
    if (isWailsAvailable()) {
      return WailsApp.SelectResumeFile();
    }
    return { cancelled: true };
  },

  runOnboarding: async (resumeText: string, jdText: string, apiKey: string) => {
    if (isWailsAvailable()) {
      return WailsApp.RunOnboarding(resumeText, jdText, apiKey);
    }
    return httpFallback('/api/pipeline/onboard', 'POST', {
      resume_text: resumeText,
      jd_text: jdText,
      api_key: apiKey,
    });
  },

  runFitAnalysis: async (profile: any, jdAnalysis: any) => {
    if (isWailsAvailable()) {
      return WailsApp.RunFitAnalysis(profile, jdAnalysis);
    }
    return httpFallback('/api/pipeline/fit-analysis', 'POST', { profile, jd_analysis: jdAnalysis });
  },

  generateQuestionBank: async (jdAnalysis: any, profile: any, fitReport: any) => {
    if (isWailsAvailable()) {
      return WailsApp.GenerateQuestionBank(jdAnalysis, profile, fitReport);
    }
    return httpFallback('/api/pipeline/question-bank', 'POST', {
      jd_analysis: jdAnalysis,
      profile,
      fit_report: fitReport,
    });
  },

  generateOnlineTest: async (questionBank: any, jdAnalysis: any) => {
    if (isWailsAvailable()) {
      return WailsApp.GenerateOnlineTest(questionBank, jdAnalysis);
    }
    return httpFallback('/api/pipeline/online-test', 'POST', {
      question_bank: questionBank,
      jd_analysis: jdAnalysis,
    });
  },

  scoreOnlineTest: async (questions: any[], userAnswers: Record<string, string>) => {
    if (isWailsAvailable()) {
      return WailsApp.ScoreOnlineTest(questions, userAnswers);
    }
    return httpFallback('/api/pipeline/score-test', 'POST', {
      test_questions: questions,
      user_answers: userAnswers,
    });
  },

  generateFeedback: async (fitReport: any, testResults: any, candidateName: string) => {
    if (isWailsAvailable()) {
      return WailsApp.GenerateFeedback(fitReport, testResults, candidateName);
    }
    return httpFallback('/api/pipeline/feedback', 'POST', {
      fit_report: fitReport,
      test_results: testResults,
      candidate_name: candidateName,
    });
  },

  generateCurriculum: async (feedback: any, jdAnalysis: any) => {
    if (isWailsAvailable()) {
      return WailsApp.GenerateCurriculum(feedback, jdAnalysis);
    }
    return httpFallback('/api/pipeline/curriculum', 'POST', {
      feedback,
      jd_analysis: jdAnalysis,
    });
  },

  toggleCurriculumTask: async (sessionId: string, dayNumber: number, taskId: string, completed: boolean) => {
    if (isWailsAvailable()) {
      return WailsApp.ToggleCurriculumTask(sessionId, dayNumber, taskId, completed);
    }
    return httpFallback('/api/curriculum/toggle-task', 'POST', {
      session_id: sessionId,
      day_number: dayNumber,
      task_id: taskId,
      completed,
    });
  },

  transcribeAudio: async (audioBase64: string) => {
    if (isWailsAvailable()) {
      return WailsApp.TranscribeAudio(audioBase64);
    }
    return httpFallback('/api/voice/transcribe', 'POST', { audio_base64: audioBase64 });
  },

  exportPdf: async (docType: string, fitReport: any, candidateName: string, roleTitle: string) => {
    if (isWailsAvailable()) {
      return WailsApp.ExportPDF(docType, fitReport, candidateName, roleTitle);
    }
    return httpFallback('/api/export/pdf', 'POST', {
      type: docType,
      fit_report: fitReport,
      candidate_name: candidateName,
      role_title: roleTitle,
    });
  },

  listSessions: async () => {
    if (isWailsAvailable()) {
      return WailsApp.ListSessions();
    }
    return httpFallback('/api/sessions', 'GET');
  },

  loadSession: async (sessionId: string) => {
    if (isWailsAvailable()) {
      return WailsApp.LoadSession(sessionId);
    }
    return httpFallback(`/api/sessions/${sessionId}`, 'GET');
  },
};
