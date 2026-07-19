import { useEffect, useCallback, useState } from 'react';
import { useWebSocket } from './hooks/useWebSocket';
import { useShutong } from './hooks/useShutong';
import { ProjectSelector } from './components/ProjectSelector';
import { MessageList } from './components/MessageList';
import { ChatInput } from './components/ChatInput';
import { FileTreePanel } from './components/FileTreePanel';
import { StatusPanel } from './components/StatusPanel';
import type { Phase } from './types';

const WS_BASE = import.meta.env.VITE_WS_URL || 'ws://localhost:8001/ws/chat';

export default function App() {
  const { connected, error, connect, disconnect, send, onMessage } = useWebSocket();
  const [projectPath, setProjectPath] = useState<string | null>(null);
  const { state, addMessage, setPhase, setLoading, clearSession } = useShutong(projectPath);
  const [showSelector, setShowSelector] = useState(true);
  const [fileTreeKey, setFileTreeKey] = useState(0);
  const [confirmedFiles, setConfirmedFiles] = useState<Set<string>>(new Set());

  const handleProjectConfirm = useCallback(
    (path: string) => {
      setProjectPath(path);
      setConfirmedFiles(new Set());
      connect(WS_BASE, () => {
        send('init_project', { rootPath: path });
      });
    },
    [connect, send]
  );

  const handleSwitchProject = useCallback(() => {
    disconnect();
    setShowSelector(true);
    setProjectPath(null);
    setConfirmedFiles(new Set());
  }, [disconnect]);

  useEffect(() => {
    if (!connected || !showSelector) return;
    setShowSelector(false);
  }, [connected, showSelector]);

  useEffect(() => {
    const cleanup = onMessage((data) => {
      const { type, payload } = data;

      switch (type) {
        case 'understanding':
          addMessage('understanding', payload);
          setLoading(false);
          break;
        case 'ai':
          addMessage('ai', payload);
          setLoading(false);
          break;
        case 'question':
          addMessage('question', payload);
          setLoading(false);
          break;
        case 'file_draft':
          addMessage('file_draft', payload);
          setLoading(false);
          break;
        case 'file_confirmed':
          addMessage('file_confirmed', payload);
          setConfirmedFiles((prev) => new Set([...prev, payload.path]));
          setFileTreeKey((k) => k + 1);
          break;
        case 'spec_draft':
          addMessage('spec_draft', payload);
          setLoading(false);
          break;
        case 'spec_locked':
          addMessage('spec_locked', payload);
          setLoading(false);
          setFileTreeKey((k) => k + 1);
          break;
        case 'file_tree':
        case 'file_updated':
          setFileTreeKey((k) => k + 1);
          break;
        case 'system':
          addMessage('system', payload);
          break;
        case 'error':
          addMessage('error', payload);
          setLoading(false);
          break;
      }
    });
    return cleanup;
  }, [onMessage, addMessage, setPhase, setLoading]);

  const handleSend = useCallback(
    (text: string) => {
      if (!text.trim() || state.loading) return;

      if (text === '/clear') {
        clearSession();
        return;
      }

      addMessage('user', text);
      setLoading(true);
      send('chat', { text });
    },
    [state.loading, addMessage, setLoading, send, clearSession]
  );

  const handleLock = useCallback(() => {
    if (state.loading) return;
    setLoading(true);
    send('lock_spec', { confirm: true });
  }, [state.loading, send, setLoading]);

  const handleConfirmFile = useCallback(
    (path: string) => {
      setConfirmedFiles((prev) => new Set([...prev, path]));
      send('confirm_file', { path });
      setFileTreeKey((k) => k + 1);
    },
    [send]
  );

  const handleReviseFile = useCallback(
    (path: string, feedback: string) => {
      setLoading(true);
      send('revise_file', { path, feedback });
    },
    [send, setLoading]
  );

  const handlePreview = useCallback(
    (path: string) => {
      if (!projectPath) return;
      window.open(
        `/api/file/read?path=${encodeURIComponent(projectPath)}&file_path=${encodeURIComponent(path)}`,
        '_blank'
      );
    },
    [projectPath]
  );

  if (showSelector) {
    return <ProjectSelector onConfirm={handleProjectConfirm} />;
  }

  return (
    <div className="h-full flex bg-gray-100">
      <FileTreePanel
        projectPath={projectPath || '.'}
        onPreview={handlePreview}
        refreshKey={fileTreeKey}
      />

      <div className="flex-1 flex flex-col max-w-3xl mx-auto bg-white shadow-lg">
        <div className="flex items-center justify-between px-4 py-2 bg-white border-b border-gray-200">
          <div className="flex items-center gap-2">
            <span className={`w-2 h-2 rounded-full ${connected ? 'bg-green-400' : 'bg-red-400'}`} />
            <span className="text-sm font-medium text-gray-700">书童V1</span>
            {projectPath && (
              <span className="text-xs text-gray-400 max-w-[200px] truncate">{projectPath}</span>
            )}
            {error && <span className="text-xs text-red-500">{error}</span>}
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={handleSwitchProject}
              className="text-xs text-gray-400 hover:text-gray-600"
            >
              切换项目
            </button>
          </div>
        </div>

        <MessageList
          messages={state.messages}
          confirmedFiles={confirmedFiles}
          onLock={handleLock}
          onConfirmFile={handleConfirmFile}
          onReviseFile={handleReviseFile}
        />

        <ChatInput
          loading={state.loading}
          onSend={handleSend}
        />
      </div>

      <StatusPanel
        messages={state.messages}
        phase={state.phase}
        loading={state.loading}
      />
    </div>
  );
}
