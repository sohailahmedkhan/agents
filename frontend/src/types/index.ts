export interface AgentAnalysisOption {
  key: string;
  label: string;
  description: string;
}

export interface AgentAnalysisSection {
  key: string;
  title: string;
  summary: string;
  status: string;
  data: unknown;
}

export interface AgentChatResponse {
  summary?: string;
  llm_summary?: {
    text?: string;
    error?: string;
  };
  analysis_sections?: AgentAnalysisSection[];
}
