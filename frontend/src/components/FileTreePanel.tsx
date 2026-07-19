import { useState, useEffect, useCallback } from 'react';

interface FileItem {
  path: string;
  name: string;
  status: string;
  exists: boolean;
  type: string;
}

interface Props {
  projectPath: string;
  onPreview: (path: string) => void;
  refreshKey?: number;
}

const STATUS_LABEL: Record<string, { label: string; color: string }> = {
  confirmed: { label: '已确认', color: 'text-green-600' },
  empty: { label: '待完善', color: 'text-gray-400' },
  pending: { label: '待确认', color: 'text-yellow-600' },
  locked: { label: '已锁定', color: 'text-blue-600' },
  updated: { label: '有更新', color: 'text-orange-600' },
};

export function FileTreePanel({ projectPath, onPreview, refreshKey }: Props) {
  const [files, setFiles] = useState<FileItem[]>([]);
  const [loading, setLoading] = useState(false);

  const fetchFiles = useCallback(async () => {
    setLoading(true);
    try {
      const resp = await fetch(
        `/api/shutong/files?path=${encodeURIComponent(projectPath)}`
      );
      const data = await resp.json();
      setFiles(data.files || []);
    } catch {
      setFiles([]);
    }
    setLoading(false);
  }, [projectPath]);

  useEffect(() => {
    if (projectPath) fetchFiles();
  }, [projectPath, fetchFiles, refreshKey]);

  return (
    <div className="w-52 bg-gray-50 border-r border-gray-200 flex flex-col h-full">
      <div className="px-3 py-2 border-b border-gray-200 flex items-center justify-between">
        <span className="text-xs font-medium text-gray-600">项目上下文</span>
        <button
          onClick={fetchFiles}
          disabled={loading}
          className="text-xs text-blue-500 hover:underline disabled:text-gray-400"
        >
          刷新
        </button>
      </div>

      <div className="flex-1 overflow-y-auto px-2 py-1">
        {files.map((f) => {
          const st = STATUS_LABEL[f.status] || STATUS_LABEL.empty;
          return (
            <div
              key={f.path}
              onClick={() => onPreview(f.path)}
              className="flex items-center gap-1.5 px-2 py-1 rounded cursor-pointer hover:bg-gray-200 group"
            >
              <span className="text-xs text-gray-500">
                {f.type === 'directory' ? '📁' : '📄'}
              </span>
              <span className="flex-1 text-xs text-gray-700 truncate">
                {f.name}
              </span>
              <span className={`text-[10px] ${st.color} opacity-0 group-hover:opacity-100 transition-opacity`}>
                {st.label}
              </span>
            </div>
          );
        })}

        {files.length === 0 && !loading && (
          <p className="text-xs text-gray-400 px-2 py-2">暂无文件</p>
        )}
      </div>
    </div>
  );
}
