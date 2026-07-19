export type Phase = 'IDLE' | 'SPEC_DRAFT' | 'LOCKED' | 'DEVELOPING';

export type MessageType =
  | 'user'
  | 'understanding'
  | 'ai'
  | 'question'
  | 'file_draft'
  | 'file_confirmed'
  | 'spec_draft'
  | 'spec_locked'
  | 'system'
  | 'error';

export interface QuestionPayload {
  id: string;
  title: string;
  description: string;
  options: string[];
  total: number;
  current: number;
  target_file?: string;
}

export interface FileDraftPayload {
  path: string;
  content: string;
}

export interface Message {
  id: string;
  type: MessageType;
  payload: any;
}

export interface AppState {
  phase: Phase;
  messages: Message[];
  inputEnabled: boolean;
  inputPlaceholder: string;
  loading: boolean;
}
