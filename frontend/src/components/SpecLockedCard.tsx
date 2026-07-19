interface Props {
  filePath: string;
}

export function SpecLockedCard({ filePath }: Props) {
  return (
    <div className="mb-4 bg-blue-50 border-l-4 border-blue-400 rounded-r-lg p-4">
      <p className="text-sm font-medium text-blue-700 mb-1">Spec已锁定</p>
      <p className="text-xs text-gray-600 mb-2">文件: {filePath}</p>
      <p className="text-xs text-blue-600">
        输入 /dev 开始开发，或提出新需求开始下一轮
      </p>
    </div>
  );
}
