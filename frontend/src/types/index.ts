export type GoalStatus = 'PENDING' | 'IN_PROGRESS' | 'COMPLETED' | 'BLOCKED';

export interface PlanGoal {
  id: string;
  description: string;
  status: GoalStatus;
  evidence_slot?: string;
}

export interface ToolCallItem {
  id: string;
  step?: number;
  tool: string;
  arguments: Record<string, any>;
  rationale: string;
  status?: 'SUCCESS' | 'ERROR' | 'TIMEOUT' | 'POLICY_DENIED' | 'PENDING';
  summary?: string;
  timestamp: number;
}

export interface ReflectionItem {
  id: string;
  trigger: string;
  diagnosis: string;
  next_approach: string;
  timestamp: number;
}

export interface EvidenceItem {
  id: string;
  file_path: string;
  start_line: number;
  end_line: number;
  content_hash: string;
  snippet: string;
  tool_source: string;
  is_direct: boolean;
}

export interface FindingItem {
  id: string;
  claim: string;
  evidence_ids: string[];
  confidence: 'CONFIRMED' | 'INFERRED' | 'NOT_FOUND';
  slot_id: string;
}

export interface ClarificationPrompt {
  type: string;
  question: string;
  investigation_id?: string;
  clarification_count?: number;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: number;
  toolCalls?: ToolCallItem[];
  plan?: PlanGoal[];
  reflections?: ReflectionItem[];
}

export interface ChatSession {
  id: string;
  title: string;
  createdAt: number;
  updatedAt: number;
  maxSteps: number;
  messages: ChatMessage[];
  state: InvestigationState;
}

export function createEmptyInvestigation(partial?: Partial<InvestigationState>): InvestigationState {
  return {
    investigation_id: '',
    status: 'IDLE',
    repo_path: '',
    query: '',
    plan: [],
    plan_version: 1,
    toolCalls: [],
    reflections: [],
    evidenceStore: [],
    findings: [],
    tokens: [],
    limitations: [],
    clarificationPrompt: null,
    ...partial,
  };
}

export interface InvestigationState {
  investigation_id: string;
  status: 'IDLE' | 'INITIALIZED' | 'RUNNING' | 'PAUSED' | 'COMPLETED' | 'FAILED' | 'SUFFICIENT' | 'PARTIAL';
  currentNode?: string;
  repo_path: string;
  query: string;
  commit_sha?: string;
  query_type?: string;
  plan: PlanGoal[];
  plan_version: number;
  toolCalls: ToolCallItem[];
  reflections: ReflectionItem[];
  evidenceStore: EvidenceItem[];
  findings: FindingItem[];
  tokens: string[];
  final_answer?: string;
  limitations: string[];
  clarificationPrompt?: ClarificationPrompt | null;
  error?: string;
}

