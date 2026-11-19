import React, { useState, useEffect } from 'react';
import { RefreshCw } from 'lucide-react';
import { API } from './services/api';
import { AppState } from './types';
import { Header } from './components/Header';
import { Sidebar } from './components/Sidebar';
import { Stepper } from './components/Stepper';

import { Step1Upload } from './pages/Step1Upload';
import { Step2FitReport } from './pages/Step2FitReport';
import { Step3QuestionBank } from './pages/Step3QuestionBank';
import { Step4OnlineTest } from './pages/Step4OnlineTest';
import { Step5Results } from './pages/Step5Results';
import { Step6Curriculum } from './pages/Step6Curriculum';

export const App: React.FC = () => {
  const [state, setState] = useState<AppState>({
    currentPage: '01_upload',
    apiKey: '',
    isKeyValid: false,
    resumeText: '',
    jdText: '',
    sessionId: `session_${Date.now()}`,
    profile: null,
    jdAnalysis: null,
    cultureFit: null,
    fitReport: null,
    questionBank: null,
    onlineTest: null,
    testResults: null,
    feedback: null,
    curriculum: null,
    telemetry: null,
    loading: false,
    loadingMessage: '',
  });

  const [savedSessions, setSavedSessions] = useState<any[]>([]);

  // Initial telemetry and health probe
  useEffect(() => {
    refreshTelemetry();
    loadPastSessions();
  }, []);

  const refreshTelemetry = async () => {
    try {
      const stats = await API.getTelemetry();
      setState((prev) => ({ ...prev, telemetry: stats }));
    } catch (e) {
      // Sidecar might still be booting
    }
  };

  const loadPastSessions = async () => {
    try {
      const res = await API.listSessions();
      if (res && res.sessions) {
        setSavedSessions(res.sessions);
      }
    } catch (e) {}
  };

  const handleValidateKey = async (key: string): Promise<boolean> => {
    try {
      const res = await API.validateApiKey(key);
      if (res && res.valid) {
        setState((prev) => ({ ...prev, apiKey: key, isKeyValid: true }));
        await refreshTelemetry();
        return true;
      }
      return false;
    } catch (err) {
      return false;
    }
  };

  const handleRunFastTrack = async () => {
    setState((prev) => ({
      ...prev,
      loading: true,
      loadingMessage: 'Analyzing Resume & Job Description requirements...',
    }));

    try {
      // Step 1: Onboard
      const onboardRes = await API.runOnboarding(state.resumeText, state.jdText, state.apiKey);
      setState((prev) => ({
        ...prev,
        profile: onboardRes.profile,
        jdAnalysis: onboardRes.jd_analysis,
        cultureFit: onboardRes.culture_fit,
        sessionId: onboardRes.session_id || prev.sessionId,
        loadingMessage: 'Evaluating Strategic Role Fit & Generating 4-Column Matrix...',
      }));

      // Step 2: Fit Analysis
      const fitRes = await API.runFitAnalysis(onboardRes.profile, onboardRes.jd_analysis);
      setState((prev) => ({
        ...prev,
        fitReport: fitRes.fit_report,
        loadingMessage: 'Synthesizing 100% Checklist-Covered Question Bank...',
      }));

      // Step 3: Question Bank
      const qbRes = await API.generateQuestionBank(
        onboardRes.jd_analysis,
        onboardRes.profile,
        fitRes.fit_report
      );
      setState((prev) => ({
        ...prev,
        questionBank: qbRes.question_bank,
        currentPage: '02_fit_report',
        loading: false,
      }));

      await refreshTelemetry();
      await loadPastSessions();
    } catch (err: any) {
      alert(`Error running Fast Track: ${err.message}`);
      setState((prev) => ({ ...prev, loading: false }));
    }
  };

  const handleRunFullPipeline = async () => {
    setState((prev) => ({
      ...prev,
      loading: true,
      loadingMessage: 'Executing Full Multi-Agent Pipeline (Steps 1 to 6)...',
    }));

    try {
      // 1. Onboarding
      const onboardRes = await API.runOnboarding(state.resumeText, state.jdText, state.apiKey);
      // 2. Fit Analysis
      setState((prev) => ({ ...prev, loadingMessage: 'Generating Strategic Fit Report...' }));
      const fitRes = await API.runFitAnalysis(onboardRes.profile, onboardRes.jd_analysis);
      // 3. Question Bank
      setState((prev) => ({ ...prev, loadingMessage: 'Building 100% Checklist-Covered Question Bank...' }));
      const qbRes = await API.generateQuestionBank(
        onboardRes.jd_analysis,
        onboardRes.profile,
        fitRes.fit_report
      );
      // 4. Online Test Generation
      setState((prev) => ({ ...prev, loadingMessage: 'Assembling 30-MCQ Timed Examination...' }));
      const testRes = await API.generateOnlineTest(qbRes.question_bank, onboardRes.jd_analysis);

      setState((prev) => ({
        ...prev,
        profile: onboardRes.profile,
        jdAnalysis: onboardRes.jd_analysis,
        cultureFit: onboardRes.culture_fit,
        fitReport: fitRes.fit_report,
        questionBank: qbRes.question_bank,
        onlineTest: testRes.online_test,
        currentPage: '02_fit_report',
        loading: false,
      }));

      await refreshTelemetry();
      await loadPastSessions();
    } catch (err: any) {
      alert(`Error executing Full Pipeline: ${err.message}`);
      setState((prev) => ({ ...prev, loading: false }));
    }
  };

  const handleSubmitOnlineTest = async (userAnswers: Record<string, string>) => {
    if (!state.onlineTest) return;
    setState((prev) => ({
      ...prev,
      loading: true,
      loadingMessage: 'Scoring 30-MCQ Examination & Computing Topic Accuracies...',
    }));

    try {
      const scoreRes = await API.scoreOnlineTest(state.onlineTest.questions, userAnswers);
      setState((prev) => ({
        ...prev,
        testResults: scoreRes.test_results,
        loadingMessage: 'Synthesizing 45/55 Composite Score & Diagnostic Roadmap...',
      }));

      // Feedback Diagnostics
      const fbRes = await API.generateFeedback(
        state.fitReport,
        scoreRes.test_results,
        state.profile?.name || 'Candidate'
      );
      setState((prev) => ({
        ...prev,
        feedback: fbRes.feedback,
        loadingMessage: 'Generating Personalized 7-Day Micro-Curriculum...',
      }));

      // Micro Curriculum
      const currRes = await API.generateCurriculum(fbRes.feedback, state.jdAnalysis);
      setState((prev) => ({
        ...prev,
        curriculum: currRes.curriculum,
        currentPage: '05_results',
        loading: false,
      }));

      await refreshTelemetry();
    } catch (err: any) {
      alert(`Error scoring test: ${err.message}`);
      setState((prev) => ({ ...prev, loading: false }));
    }
  };

  const handleExportFitPdf = async () => {
    try {
      const res = await API.exportPdf(
        'fit_report',
        state.fitReport,
        state.profile?.name || 'Candidate',
        state.jdAnalysis?.role_title || 'Target Role'
      );
      downloadBase64Pdf(res.pdf_base64, res.filename || 'InterviewIQ_FitReport.pdf');
    } catch (err: any) {
      alert(`Failed to export PDF: ${err.message}`);
    }
  };

  const handleExportDossierPdf = async () => {
    try {
      const res = await API.exportPdf(
        'full_dossier',
        state.fitReport,
        state.profile?.name || 'Candidate',
        state.jdAnalysis?.role_title || 'Target Role'
      );
      downloadBase64Pdf(res.pdf_base64, res.filename || 'InterviewIQ_FullDossier.pdf');
    } catch (err: any) {
      alert(`Failed to export Dossier PDF: ${err.message}`);
    }
  };

  const downloadBase64Pdf = (b64: string, filename: string) => {
    const link = document.createElement('a');
    link.href = `data:application/pdf;base64,${b64}`;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const handleResetSession = () => {
    if (window.confirm('Reset current session and clear all evaluation stages?')) {
      setState((prev) => ({
        ...prev,
        currentPage: '01_upload',
        resumeText: '',
        jdText: '',
        sessionId: `session_${Date.now()}`,
        profile: null,
        jdAnalysis: null,
        cultureFit: null,
        fitReport: null,
        questionBank: null,
        onlineTest: null,
        testResults: null,
        feedback: null,
        curriculum: null,
      }));
    }
  };

  const handleLoadSession = async (sessId: string) => {
    try {
      const res = await API.loadSession(sessId);
      if (res && res.state) {
        const s = res.state;
        setState((prev) => ({
          ...prev,
          sessionId: sessId,
          profile: s.profile || null,
          jdAnalysis: s.jd_analysis || null,
          fitReport: s.fit_report || null,
          questionBank: s.question_bank || null,
          onlineTest: s.online_test || null,
          testResults: s.test_results || null,
          feedback: s.feedback || null,
          curriculum: s.curriculum || null,
          currentPage: s.feedback ? '05_results' : s.fit_report ? '02_fit_report' : '01_upload',
        }));
      }
    } catch (err: any) {
      alert(`Failed to load session: ${err.message}`);
    }
  };

  const stepNumberMap: Record<string, number> = {
    '01_upload': 1,
    '02_fit_report': 2,
    '03_question_bank': 3,
    '04_online_test': 4,
    '05_results': 5,
    '06_curriculum': 6,
  };

  const currentStepNum = stepNumberMap[state.currentPage] || 1;

  const navigateToStepNum = (stepNum: number) => {
    const pageKeys = [
      '01_upload',
      '02_fit_report',
      '03_question_bank',
      '04_online_test',
      '05_results',
      '06_curriculum',
    ];
    const targetKey = pageKeys[stepNum - 1] as any;
    setState((prev) => ({ ...prev, currentPage: targetKey }));
  };

  return (
    <div className="min-h-screen flex flex-col bg-canvas">
      {/* Header Bar */}
      <Header
        directmlInfo={state.telemetry?.directml}
        activeModel={state.isKeyValid ? 'gemini-2.5-flash' : 'API Key Required'}
        onResetSession={handleResetSession}
      />

      {/* Main Body */}
      <div className="flex-1 flex overflow-hidden">
        {/* Sidebar */}
        <Sidebar
          currentPage={state.currentPage}
          onNavigate={(pageId) => setState((prev) => ({ ...prev, currentPage: pageId }))}
          apiKey={state.apiKey}
          isKeyValid={state.isKeyValid}
          onValidateKey={handleValidateKey}
          telemetry={state.telemetry}
          savedSessions={savedSessions}
          onLoadSession={handleLoadSession}
        />

        {/* Dynamic Page Content */}
        <main className="flex-1 overflow-y-auto p-6 md:p-8 max-w-7xl mx-auto w-full">
          {/* Stepper Header */}
          <Stepper currentStep={currentStepNum} onStepClick={navigateToStepNum} />

          {/* Render Active View */}
          {state.currentPage === '01_upload' && (
            <Step1Upload
              apiKey={state.apiKey}
              isKeyValid={state.isKeyValid}
              resumeText={state.resumeText}
              jdText={state.jdText}
              onResumeChange={(val) => setState((prev) => ({ ...prev, resumeText: val }))}
              onJdChange={(val) => setState((prev) => ({ ...prev, jdText: val }))}
              onRunFastTrack={handleRunFastTrack}
              onRunFullPipeline={handleRunFullPipeline}
              isLoading={state.loading}
            />
          )}

          {state.currentPage === '02_fit_report' && (
            <Step2FitReport
              fitReport={state.fitReport}
              candidateName={state.profile?.name || 'Candidate'}
              roleTitle={state.jdAnalysis?.role_title || 'Target Role'}
              onExportPdf={handleExportFitPdf}
              onNextStep={() => setState((prev) => ({ ...prev, currentPage: '03_question_bank' }))}
            />
          )}

          {state.currentPage === '03_question_bank' && (
            <Step3QuestionBank
              questionBank={state.questionBank}
              onNextStep={() => setState((prev) => ({ ...prev, currentPage: '04_online_test' }))}
            />
          )}

          {state.currentPage === '04_online_test' && (
            <Step4OnlineTest
              onlineTest={state.onlineTest}
              onSubmitTest={handleSubmitOnlineTest}
              isSubmitting={state.loading}
              hasResults={!!state.testResults}
              onNextStep={() => setState((prev) => ({ ...prev, currentPage: '05_results' }))}
            />
          )}

          {state.currentPage === '05_results' && (
            <Step5Results
              feedback={state.feedback}
              testResults={state.testResults}
              candidateName={state.profile?.name || 'Candidate'}
              roleTitle={state.jdAnalysis?.role_title || 'Target Role'}
              onExportDossierPdf={handleExportDossierPdf}
              onNextStep={() => setState((prev) => ({ ...prev, currentPage: '06_curriculum' }))}
            />
          )}

          {state.currentPage === '06_curriculum' && (
            <Step6Curriculum
              curriculum={state.curriculum}
              sessionId={state.sessionId}
            />
          )}
        </main>
      </div>

      {/* Global Async Loading Overlay */}
      {state.loading && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-surface border border-border p-6 rounded-2xl shadow-xl max-w-md w-full text-center space-y-4">
            <div className="w-12 h-12 mx-auto rounded-full bg-primary-light flex items-center justify-center text-primary">
              <RefreshCw size={24} className="animate-spin" />
            </div>
            <div>
              <h3 className="text-base font-extrabold text-heading">Multi-Agent Processing</h3>
              <p className="text-xs text-muted mt-1 leading-relaxed">{state.loadingMessage}</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
