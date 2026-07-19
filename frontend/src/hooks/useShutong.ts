import { useState, useCallback, useEffect } from 'react';
import type { Phase, Message, AppState } from '../types';

const STORAGE_PREFIX = 'shutong_session_';
const MAX_MESSAGES = 50;

function getStorageKey(projectPath: string): string {
  return `${STORAGE_PREFIX}${projectPath}`;
}

function loadSession(projectPath: string): Partial<AppState> | null {
  try {
    const raw = localStorage.getItem(getStorageKey(projectPath));
    if (!raw) return null;
    const data = JSON.parse(raw);
    if (data.messages && data.messages.length > 0) {
      // 去重：每个文件只保留最新的 file_confirmed
      const lastConfirmed = new Map<string, number>();
      data.messages.forEach((m: Message, i: number) => {
        if (m.type === 'file_confirmed' && m.payload?.path) {
          lastConfirmed.set(m.payload.path, i);
        }
      });
      data.messages = data.messages.filter((m: Message, i: number) => {
        if (m.type === 'file_confirmed' && m.payload?.path) {
          return lastConfirmed.get(m.payload.path) === i;
        }
        return true;
      });
      return data;
    }
    return null;
  } catch {
    return null;
  }
}

function saveSession(projectPath: string, state: Partial<AppState>): void {
  try {
    const toSave = {
      messages: (state.messages || []).slice(-MAX_MESSAGES),
      phase: state.phase,
      lastMessageTime: Date.now(),
    };
    localStorage.setItem(getStorageKey(projectPath), JSON.stringify(toSave));
  } catch {
    // localStorage full, silently ignore
  }
}

function clearSession(projectPath: string): void {
  localStorage.removeItem(getStorageKey(projectPath));
}

const initialState: AppState = {
  phase: 'IDLE',
  messages: [],
  inputEnabled: true,
  inputPlaceholder: '输入消息...',
  loading: false,
};

export function useShutong(projectPath: string | null) {
  const [state, setState] = useState<AppState>(initialState);

  // 项目切换时加载或重置session
  useEffect(() => {
    if (projectPath) {
      const saved = loadSession(projectPath);
      if (saved) {
        setState((prev) => ({
          ...prev,
          messages: saved.messages || [],
          phase: saved.phase || 'IDLE',
        }));
      } else {
        setState(initialState);
      }
    } else {
      setState(initialState);
    }
  }, [projectPath]);

  // 每次状态变化自动保存
  useEffect(() => {
    if (projectPath && state.messages.length > 0) {
      saveSession(projectPath, state);
    }
  }, [projectPath, state.messages, state.phase]);

  const addMessage = useCallback((type: Message['type'], payload: any) => {
    const msg: Message = {
      id: `${Date.now()}-${Math.random().toString(36).slice(2, 7)}`,
      type,
      payload,
    };
    setState((prev) => {
      let msgs = [...prev.messages, msg];
      // 收到新file_draft时，清除同路径的旧file_confirmed
      if (type === 'file_draft' && payload?.path) {
        msgs = msgs.filter((m) =>
          !(m.type === 'file_confirmed' && m.payload?.path === payload.path)
        );
      }
      return { ...prev, messages: msgs };
    });
    return msg;
  }, []);

  const setPhase = useCallback((phase: Phase) => {
    setState((prev) => ({ ...prev, phase }));
  }, []);

  const setLoading = useCallback((loading: boolean) => {
    setState((prev) => ({ ...prev, loading, inputEnabled: !loading }));
  }, []);

  const handleClearSession = useCallback(() => {
    if (projectPath) clearSession(projectPath);
    setState(initialState);
  }, [projectPath]);

  return {
    state,
    addMessage,
    setPhase,
    setLoading,
    clearSession: handleClearSession,
  };
}
