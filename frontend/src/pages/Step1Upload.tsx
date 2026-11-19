import React, { useState } from 'react';
import { Upload, FileText, CheckCircle, AlertCircle, ArrowRight, Play, Sparkles } from 'lucide-react';
import { API } from '../services/api';
import { Badge } from '../components/Badge';

interface Step1UploadProps {
  apiKey: string;
  isKeyValid: boolean;
  resumeText: string;
  jdText: string;
  onResumeChange: (val: string) => void;
  onJdChange: (val: string) => void;
  onRunFastTrack: () => void;
  onRunFullPipeline: () => void;
  isLoading: boolean;
}

const SAMPLE_RESUMES = {
  ai_engineer: `NITISH KUMAR\nSenior AI & Machine Learning Engineer\nEmail: nitish@example.com | GitHub: github.com/nitish\n\nPROFESSIONAL SUMMARY\nExperienced AI Engineer with 6+ years designing, training, and deploying large language models, agentic workflows, and microservice architectures. Expert in Python, PyTorch, Go, LangChain, Google Gemini API, and ONNX Runtime DirectML.\n\nTECHNICAL SKILLS\n- Languages: Python, Go, TypeScript, SQL\n- AI/ML: PyTorch, TensorFlow, Hugging Face, DirectML, LangChain, RAG architectures\n- Cloud/DevOps: Docker, Kubernetes, AWS, GCP, CI/CD, Git\n\nPROFESSIONAL EXPERIENCE\nSenior Machine Learning Architect | Apex Innovations (2022 - Present)\n- Led a team of 5 engineers building an enterprise multi-agent placement platform.\n- Reduced LLM latency by 45% using token-bucket rate pacing and two-tier caching.\n- Deployed DirectML hardware-accelerated local embeddings on Windows workstations.\n\nAI Systems Engineer | CloudScale Systems (2019 - 2022)\n- Developed distributed microservices in Go and Python serving 10M daily requests.\n- Built real-time speech analytics engines with WPM and filler word classification.\n\nEDUCATION\nM.S. in Computer Science | Stanford University\nB.Tech in Computer Engineering | National Institute of Technology`,

  cloud_architect: `JEEVANA REDDY\nPrincipal Cloud & Distributed Systems Architect\nEmail: jeevana@example.com | LinkedIn: linkedin.com/in/jeevana\n\nSUMMARY\nStrategic Cloud Systems Architect with 8+ years experience scaling enterprise distributed systems, Kubernetes orchestration, high-throughput microservices, and reactive frontends in TypeScript and React.\n\nCORE COMPETENCIES\n- Systems: Go, Distributed Consensus, gRPC, Kafka, Docker, Kubernetes\n- Web & Desktop: React, Vite, TypeScript, Tailwind CSS, Wails\n- Cloud: AWS (EKS, Lambda, DynamoDB), Azure, Google Cloud Platform\n\nEXPERIENCE\nPrincipal Systems Architect | Horizon Tech (2021 - Present)\n- Engineered high-availability microservice mesh handling 50,000 req/sec in Go.\n- Modernized legacy web dashboards to native Wails v2 desktop architecture.\n\nLead DevOps Engineer | DataForge (2017 - 2021)\n- Architected multi-region Kubernetes clusters with automated GitOps pipelines.\n\nEDUCATION\nMBA in Digital Transformation | Premier Business School\nB.E. in Information Technology`,
};

const SAMPLE_JDS = {
  ai_engineer: `Job Title: Senior AI & Placement Systems Engineer\nCompany: Google DeepMind Enterprise\nLocation: Remote / Hybrid\n\nROLE OVERVIEW\nWe are looking for a Senior AI & Placement Systems Engineer to architect next-generation multi-agent assessment systems. You will develop decoupled agents in Python and Go, integrate Google Gemini models, build real-time speech evaluators, and deploy DirectML hardware acceleration.\n\nMANDATORY REQUIREMENTS:\n- 5+ years building production AI/ML applications and agentic workflows in Python and Go.\n- Demonstrated proficiency with Large Language Model APIs (Gemini, OpenAI, Claude).\n- Experience with DirectML, ONNX Runtime, or hardware-accelerated inference.\n- Solid knowledge of Docker, relational databases (SQLite/Postgres), and vector retrieval.\n\nPREFERRED QUALIFICATIONS:\n- Familiarity with Wails desktop applications and React/TypeScript frontends.\n- Experience designing recruitment scoring rubrics or academic evaluation pipelines.\n- Master's degree in Computer Science, AI, or related technical field.`,

  cloud_architect: `Job Title: Principal Cloud Infrastructure & Desktop Architect\nCompany: CloudNative Solutions\nLocation: San Francisco, CA / Remote\n\nROLE SUMMARY\nSeeking a seasoned Architect to lead the modernization of our core desktop client stack to Go, Wails, React, and TypeScript. You will oversee secure IPC sidecar communications, containerized microservices, and system reliability.\n\nMANDATORY SKILLS:\n- 7+ years of experience with Go, microservice architecture, and distributed systems.\n- Production expertise in React, TypeScript, and modern Tailwind CSS design systems.\n- Deep understanding of IPC protocols, process supervision, and OS windowing.\n\nPREFERRED SKILLS:\n- Experience with Python ML sidecar services and local neural network acceleration.\n- Cloud certifications in AWS or GCP.`,
};

export const Step1Upload: React.FC<Step1UploadProps> = ({
  apiKey,
  isKeyValid,
  resumeText,
  jdText,
  onResumeChange,
  onJdChange,
  onRunFastTrack,
  onRunFullPipeline,
  isLoading,
}) => {
  const [activeTab, setActiveTab] = useState<'ai' | 'cloud'>('ai');

  const loadDemo = (type: 'ai' | 'cloud') => {
    setActiveTab(type);
    onResumeChange(SAMPLE_RESUMES[type === 'ai' ? 'ai_engineer' : 'cloud_architect']);
    onJdChange(SAMPLE_JDS[type === 'ai' ? 'ai_engineer' : 'cloud_architect']);
  };

  const handleNativeFileSelect = async () => {
    try {
      const res = await API.selectResumeFile();
      if (!res.cancelled && res.content) {
        onResumeChange(res.content);
      }
    } catch (err) {
      console.error('File dialog failed:', err);
    }
  };

  return (
    <div className="space-y-6">
      {/* Hero Banner */}
      <div className="neuro-card p-6 border-l-4 border-l-primary bg-surface">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <Badge label="Candidate Diagnostics" variant="primary" />
              <Badge label="Step 1 of 6" variant="slate" />
            </div>
            <h2 className="text-xl font-extrabold text-heading">
              Step 1: Upload Resume & Job Description
            </h2>
            <p className="text-xs text-muted mt-1 max-w-2xl">
              Upload your candidate resume and target Job Description to generate comprehensive
              strategic placement intelligence across our 8-agent cognitive pipeline.
            </p>
          </div>

          {/* Quick Demo Pre-loaders */}
          <div className="flex items-center gap-2">
            <button
              onClick={() => loadDemo('ai')}
              className="px-3 py-2 bg-inset hover:bg-border text-heading rounded-xl text-xs font-bold transition-colors flex items-center gap-1.5"
            >
              <Sparkles size={14} className="text-primary" /> Senior AI Demo
            </button>
            <button
              onClick={() => loadDemo('cloud')}
              className="px-3 py-2 bg-inset hover:bg-border text-heading rounded-xl text-xs font-bold transition-colors flex items-center gap-1.5"
            >
              <Sparkles size={14} className="text-primary" /> Cloud Architect Demo
            </button>
          </div>
        </div>
      </div>

      {/* API Key Required Gatekeeper Banner */}
      {!isKeyValid && (
        <div className="neuro-card p-4 border-l-4 border-l-danger bg-danger-light/30">
          <div className="flex items-start justify-between gap-4 flex-wrap">
            <div>
              <h3 className="text-sm font-bold text-danger-dark flex items-center gap-2">
                <AlertCircle size={16} /> Google Gemini API Key Required to Begin
              </h3>
              <p className="text-xs text-muted mt-1">
                InterviewIQ leverages Google Gemini models to power its multi-agent placement
                assessment pipeline. Activate your free key in the sidebar or below to unlock candidate evaluations.
              </p>
            </div>
            <a
              href="https://aistudio.google.com/app/apikey"
              target="_blank"
              rel="noreferrer"
              className="px-4 py-2 bg-primary hover:bg-primary-dark text-white rounded-lg text-xs font-bold transition-colors"
            >
              Get Free API Key (Google AI Studio) ↗
            </a>
          </div>
        </div>
      )}

      {/* Input Columns */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Resume Column */}
        <div className="neuro-card p-5 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-muted flex items-center gap-1.5">
              <FileText size={15} className="text-primary" /> Candidate Resume
            </span>
            <button
              onClick={handleNativeFileSelect}
              className="text-xs font-bold text-primary hover:underline flex items-center gap-1"
            >
              <Upload size={13} /> Select File (PDF/DOCX/TXT)
            </button>
          </div>
          <textarea
            value={resumeText}
            onChange={(e) => onResumeChange(e.target.value)}
            placeholder="Paste candidate resume plain text here, or click Select File above..."
            rows={15}
            className="w-full p-3 text-xs rounded-xl border border-border bg-canvas text-body font-mono focus:outline-none focus:border-primary leading-relaxed resize-none"
          />
        </div>

        {/* Job Description Column */}
        <div className="neuro-card p-5 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-muted flex items-center gap-1.5">
              <FileText size={15} className="text-primary" /> Target Job Description (JD)
            </span>
            <span className="text-xs text-muted font-medium">Include mandatory skills</span>
          </div>
          <textarea
            value={jdText}
            onChange={(e) => onJdChange(e.target.value)}
            placeholder="Paste target Job Description requirements here..."
            rows={15}
            className="w-full p-3 text-xs rounded-xl border border-border bg-canvas text-body font-mono focus:outline-none focus:border-primary leading-relaxed resize-none"
          />
        </div>
      </div>

      {/* Action Execution Footer */}
      <div className="neuro-card p-4 flex flex-col sm:flex-row items-center justify-end gap-3 bg-surface">
        <button
          onClick={onRunFastTrack}
          disabled={!resumeText.trim() || !jdText.trim() || isLoading}
          className="w-full sm:w-auto px-5 py-3 rounded-xl border border-border hover:bg-inset text-xs font-extrabold text-heading disabled:opacity-50 transition-all flex items-center justify-center gap-2"
        >
          <Play size={15} className="text-primary" /> Strategic Fit & Question Bank Alone (Fast Track)
        </button>

        <button
          onClick={onRunFullPipeline}
          disabled={!resumeText.trim() || !jdText.trim() || isLoading}
          className="w-full sm:w-auto px-6 py-3 rounded-xl bg-primary hover:bg-primary-dark text-white text-xs font-extrabold disabled:opacity-50 transition-all flex items-center justify-center gap-2 shadow-glow"
        >
          <span>Perform Complete Analysis from Start till End</span>
          <ArrowRight size={15} />
        </button>
      </div>
    </div>
  );
};
