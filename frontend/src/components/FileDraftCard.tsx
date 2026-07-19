import { useState } from 'react';

interface Props {
  path: string;
  content: string;
  confirmed?: boolean;
  onConfirm: (path: string) => void;
  onRevise: (path: string, feedback: string) => void;
}

export function FileDraftCard({ path, content, confirmed, onConfirm, onRevise }: Props) {
  const [expanded, setExpanded] = useState(false);
  const [showFeedback, setShowFeedback] = useState(false);
  const [feedback, setFeedback] = useState('');

  const handleConfirm = () => {
    onConfirm(path);
  };

  const handleRevise = () => {
    if (feedback.trim()) {
      onRevise(path, feedback.trim());
      setShowFeedback(false);
      setFeedback('');
    }
  };

  if (confirmed) {
    return (
      <div className="mb-4 bg-green-50 border-l-4 border-green-400 rounded-r-lg p-4">
        <p className="text-sm font-medium text-green-700">{path} 已确认写入</p>
      </div>
    );
  }

  return (
    <div className="mb-4 bg-white border border-gray-200 rounded-lg shadow-sm overflow-hidden">
      <div className="px-4 py-2 bg-orange-50 border-b border-orange-200 flex items-center justify-between">
        <span className="text-sm font-medium text-orange-700">
          {path} 草案
        </span>
        <button
          onClick={() => setExpanded(!expanded)}
          className="text-xs text-blue-600 hover:underline"
        >
          {expanded ? '收起' : '展开'}
        </button>
      </div>

      <div className={`px-4 py-3 ${expanded ? '' : 'max-h-40 overflow-hidden'}`}>
        <pre className="text-xs text-gray-600 whitespace-pre-wrap font-mono leading-relaxed">
          {content}
        </pre>
      </div>

      {!expanded && content.length > 300 && (
        <div className="px-4 pb-2">
          <span className="text-xs text-gray-400">...(内容已折叠)</span>
        </div>
      )}

      <div className="px-4 py-3 bg-gray-50 border-t border-gray-200 flex gap-2 items-center">
        <button
          onClick={handleConfirm}
          className="px-4 py-1.5 bg-green-500 text-white text-sm rounded hover:bg-green-600 transition-colors"
        >
          确认写入
        </button>
        <button
          onClick={() => setShowFeedback(!showFeedback)}
          className="px-4 py-1.5 text-gray-600 text-sm border border-gray-300 rounded hover:bg-gray-100 transition-colors"
        >
          提修改意见
        </button>
      </div>

      {showFeedback && (
        <div className="px-4 py-3 border-t border-gray-200">
          <textarea
            value={feedback}
            onChange={(e) => setFeedback(e.target.value)}
            placeholder="请说明需要修改的内容..."
            className="w-full px-3 py-2 border border-gray-300 rounded text-sm resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
            rows={3}
          />
          <div className="mt-2 flex gap-2">
            <button
              onClick={handleRevise}
              disabled={!feedback.trim()}
              className="px-3 py-1 bg-blue-500 text-white text-sm rounded hover:bg-blue-600 disabled:opacity-40"
            >
              提交修改
            </button>
            <button
              onClick={() => setShowFeedback(false)}
              className="px-3 py-1 text-gray-500 text-sm"
            >
              取消
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
