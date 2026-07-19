import { useState, useEffect } from 'react';
import type { Phase } from '../types';

export interface Step {
  id: string;
  label: string;
  status: 'pending' | 'running' | 'done' | 'error';
}

const phaseConfig: Record<Phase, { label: string; color: string; dot: string }> = {
  IDLE: { label: '等待输入', color: 'text-gray-500', dot: 'bg-gray-300' },
  SPEC_DRAFT: { label: 'Spec待确认', color: 'text-orange-600', dot: 'bg-orange-400' },
  LOCKED: { label: '已锁定', color: 'text-blue-600', dot: 'bg-blue-400' },
  DEVELOPING: { label: '开发中', color: 'text-indigo-600', dot: 'bg-indigo-400' },
};

interface Props {
  messages: any[];
  phase: Phase;
  loading: boolean;
}

function buildSteps(messages: any[], phase: string, loading: boolean): Step[] {
  const steps: Step[] = [];
  const types = messages.map((m) => m.type);

  if (types.includes('understanding') || types.includes('question') || types.includes('ai')) {
    steps.push({ id: 'analyze', label: '分析需求', status: 'done' });
  } else if (loading) {
    steps.push({ id: 'analyze', label: '分析需求', status: 'running' });
  }

  if (types.includes('question')) {
    steps.push({ id: 'question', label: '追问确认', status: 'done' });
  } else if (loading && types.includes('understanding')) {
    steps.push({ id: 'question', label: '追问确认', status: 'running' });
  }

  if (types.includes('spec_draft')) {
    steps.push({ id: 'spec', label: '生成Spec', status: 'done' });
  } else if (phase === 'SPEC_DRAFT' && loading) {
    steps.push({ id: 'spec', label: '生成Spec', status: 'running' });
  }

  if (types.includes('spec_locked')) {
    steps.push({ id: 'lock', label: '锁定Spec', status: 'done' });
  } else if (phase === 'LOCKED' && loading) {
    steps.push({ id: 'lock', label: '锁定Spec', status: 'running' });
  }

  return steps;
}

export function StatusPanel({ messages, phase, loading }: Props) {
  const [steps, setSteps] = useState<Step[]>([]);
  const cfg = phaseConfig[phase] || phaseConfig.IDLE;

  useEffect(() => {
    setSteps(buildSteps(messages, phase, loading));
  }, [messages, phase, loading]);

  return (
    <div className="w-56 bg-gray-50 border-l border-gray-200 flex flex-col h-full">
      {/* 阶段指示器（顶部） */}
      <div className="px-3 py-2 border-b border-gray-200 flex items-center gap-2">
        <span className={`w-2.5 h-2.5 rounded-full ${cfg.dot}`} />
        <span className={`text-sm font-medium ${cfg.color}`}>{cfg.label}</span>
      </div>

      {/* 流程步骤 */}
      <div className="px-3 py-2 border-b border-gray-200">
        <span className="text-xs font-medium text-gray-500">处理流程</span>
      </div>

      <div className="flex-1 overflow-y-auto px-3 py-2 space-y-2">
        {steps.map((step) => (
          <div key={step.id} className="flex items-center gap-2 py-1.5">
            {step.status === 'running' && (
              <span className="w-3.5 h-3.5 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
            )}
            {step.status === 'done' && (
              <span className="text-green-500 text-xs">✓</span>
            )}
            {step.status === 'error' && (
              <span className="text-red-500 text-xs">✗</span>
            )}
            {step.status === 'pending' && (
              <span className="w-3.5 h-3.5 rounded-full border border-gray-300" />
            )}
            <span className={`text-xs ${
              step.status === 'running' ? 'text-blue-600 font-medium' :
              step.status === 'done' ? 'text-gray-700' :
              step.status === 'error' ? 'text-red-600' :
              'text-gray-400'
            }`}>
              {step.label}
            </span>
          </div>
        ))}

        {steps.length === 0 && (
          <p className="text-xs text-gray-400 py-2">等待操作...</p>
        )}
      </div>
    </div>
  );
}
