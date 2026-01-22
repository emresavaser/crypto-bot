'use client';

import { useBot } from '@/contexts/BotContext';
import { CheckCircle, XCircle, Circle, Cpu, AlertCircle } from 'lucide-react';

export default function ModuleStatusPanel() {
  const { modules, isRunning } = useBot();

  if (!isRunning || modules.length === 0) {
    return null;
  }

  const runningModules = modules.filter(m => m.running);
  const errorModules = modules.filter(m => m.error);
  const availableModules = modules.filter(m => m.available);

  return (
    <div className="glass-card rounded-2xl p-5">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Cpu className="w-5 h-5 text-cyan-400" />
          <h3 className="text-lg font-semibold text-white">Modul Durumu</h3>
        </div>
        <div className="flex items-center gap-2 text-sm">
          <span className="text-green-400">{runningModules.length} aktif</span>
          {errorModules.length > 0 && (
            <span className="text-red-400">{errorModules.length} hata</span>
          )}
        </div>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
        {modules.map((module) => (
          <ModuleStatusItem key={module.name} module={module} />
        ))}
      </div>

      {errorModules.length > 0 && (
        <div className="mt-4 p-3 bg-red-500/10 border border-red-500/30 rounded-xl">
          <div className="flex items-center gap-2 text-red-400 text-sm font-medium mb-2">
            <AlertCircle className="w-4 h-4" />
            Hata Detaylari
          </div>
          {errorModules.map((module) => (
            <p key={module.name} className="text-red-300/80 text-xs">
              <strong>{module.display_name}:</strong> {module.error}
            </p>
          ))}
        </div>
      )}
    </div>
  );
}

interface ModuleStatusItemProps {
  module: {
    name: string;
    display_name: string;
    available: boolean;
    running: boolean;
    error: string | null;
  };
}

function ModuleStatusItem({ module }: ModuleStatusItemProps) {
  const getStatusColor = () => {
    if (module.error) return 'from-red-500/20 to-red-600/10 border-red-500/30';
    if (module.running) return 'from-green-500/20 to-emerald-600/10 border-green-500/30';
    if (module.available) return 'from-yellow-500/20 to-orange-600/10 border-yellow-500/30';
    return 'from-gray-500/20 to-gray-600/10 border-gray-500/30';
  };

  const getIcon = () => {
    if (module.error) {
      return <XCircle className="w-4 h-4 text-red-400" />;
    }
    if (module.running) {
      return <CheckCircle className="w-4 h-4 text-green-400" />;
    }
    if (module.available) {
      return <Circle className="w-4 h-4 text-yellow-400" />;
    }
    return <XCircle className="w-4 h-4 text-gray-500" />;
  };

  const getStatusText = () => {
    if (module.error) return 'Hata';
    if (module.running) return 'Aktif';
    if (module.available) return 'Hazir';
    return 'Yok';
  };

  return (
    <div
      className={`bg-gradient-to-br ${getStatusColor()} rounded-lg p-2 flex items-center gap-2 transition-all hover:scale-[1.02]`}
      title={module.error || `${module.display_name}: ${getStatusText()}`}
    >
      {getIcon()}
      <div className="flex-1 min-w-0">
        <p className="text-white text-xs font-medium truncate">{module.display_name}</p>
        <p className={`text-[10px] ${
          module.error ? 'text-red-300' :
          module.running ? 'text-green-300' :
          module.available ? 'text-yellow-300' : 'text-gray-400'
        }`}>
          {getStatusText()}
        </p>
      </div>
    </div>
  );
}
