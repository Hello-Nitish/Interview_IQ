// Core Domain Type Definitions for InterviewIQ

export interface CandidateProfile {
  name?: string;
  summary?: string;
  education?: string[];
  skills?: string[];
  experience_years?: number;
  experience?: string[];
  projects?: string[];
  challenge_areas?: string[];
}

export interface JDRequirement {
  name: string;
  category: string;
  priority: "High" | "Medium" | "Low";
  status?: "Matched" | "Gap" | "Partial";
  evidence?: string;
}

export interface JDAnalysis {
  role_title?: string;
  company_name?: string;
  mandatory_skills?: string[];
  preferred_skills?: string[];
  domain_competencies?: string[];
  requirements?: JDRequirement[];
  raw_text?: string;
}

export interface RequirementMatchItem {
  requirement: string;
  category: string;
  evidence_status: string; // e.g. "Present: ..." or "Missing: ..."
  status: "MATCHED" | "GAP" | "PARTIAL";
}

export interface StrategicFitReport {
  overall_fit_decision?: "STRONG HIRE" | "SHORTLIST" | "CONDITIONAL" | "REJECT";
  governing_rule_citation?: string;
  decision_rationale?: string[];
  alternative_role_routing?: string[];
  technical_rating?: {
    technical_match_pct: number;
    mandatory_matched: number;
    total_mandatory: number;
  };
  experience_rating?: {
    score_out_of_10: number;
    tier_label: string;
  };
  requirements_matrix?: RequirementMatchItem[];
  gap_analysis?: {
    critical_gaps?: string[];
    secondary_gaps?: string[];
  };
}

export interface QuestionBankItem {
  id: string;
  topic: string;
  category: "Technical Deep-Dive" | "Problem Solving" | "Behavioral STAR" | "Resume Challenge" | "Gap Mitigation";
  question: string;
  expected_signal: string;
  difficulty: "Easy" | "Medium" | "Hard";
}

export interface QuestionBank {
  topic_checklist?: Array<{
    topic: string;
    coverage_status: "Gap" | "Claimed" | "Untested";
  }>;
  questions?: QuestionBankItem[];
}

export interface MCQOption {
  key: "A" | "B" | "C" | "D";
  text: string;
}

export interface MCQQuestion {
  id: string | number;
  question: string;
  topic: string;
  options: MCQOption[];
  correct_answer: string;
  rationale: string;
}

export interface TestScoreResult {
  total_score: number;
  max_score: number;
  percentage: number;
  passed: boolean;
  topic_accuracies: Array<{
    topic: string;
    correct: number;
    total: number;
    pct: number;
    status: "Strong" | "Adequate" | "Deficient";
  }>;
  review: Array<{
    question_id: string | number;
    question_text: string;
    candidate_answer: string;
    correct_answer: string;
    is_correct: boolean;
    topic: string;
    rationale: string;
  }>;
}

export interface FeedbackDiagnostics {
  composite_readiness_pct: number;
  structural_fit_score: number;
  empirical_test_score: number;
  overall_verdict: string;
  prioritized_topics_for_next_round: string[];
  topic_readiness_matrix: Array<{
    topic: string;
    fit_status: string;
    test_accuracy: number;
    readiness_level: "High" | "Medium" | "Low" | "Priority Gap";
  }>;
  revision_roadmap_48h: Array<{
    hour_block: string;
    focus_topic: string;
    action_item: string;
    concrete_exercise: string;
  }>;
}

export interface CurriculumTask {
  id: string;
  title: string;
  description: string;
  resource_link?: string;
  resource_title?: string;
  completed: boolean;
  estimated_minutes: number;
}

export interface CurriculumDay {
  day_number: number;
  day_title: string;
  core_competency: string;
  tasks: CurriculumTask[];
}

export interface MicroCurriculum {
  curriculum_id: string;
  role_target: string;
  candidate_name: string;
  days: CurriculumDay[];
}

export interface TelemetryStats {
  session_calls: number;
  session_cache_hits: number;
  daily_limit: number;
  current_rpm: number;
  rate_status: string;
  status_color: string;
  cache_savings_pct: number;
  directml?: {
    directml_available: boolean;
    provider: string;
    device_name: string;
    device_count: number;
    platform: string;
  };
}

export interface AppState {
  currentPage: "01_upload" | "02_fit_report" | "03_question_bank" | "04_online_test" | "05_results" | "06_curriculum";
  apiKey: string;
  isKeyValid: boolean;
  resumeText: string;
  jdText: string;
  sessionId: string;
  profile: CandidateProfile | null;
  jdAnalysis: JDAnalysis | null;
  cultureFit: any;
  fitReport: StrategicFitReport | null;
  questionBank: QuestionBank | null;
  onlineTest: { questions: MCQQuestion[]; total_questions: number } | null;
  testResults: TestScoreResult | null;
  feedback: FeedbackDiagnostics | null;
  curriculum: MicroCurriculum | null;
  telemetry: TelemetryStats | null;
  loading: boolean;
  loadingMessage: string;
}
