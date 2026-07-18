/**
 * EmptyState.tsx — Placeholder shown before research starts.
 */

import { FlaskConical, Globe, BookOpen, FileText } from 'lucide-react'

export function ThinkingEmptyState() {
  return (
    <div className="flex flex-col items-center justify-center h-full text-center px-6 py-8">
      <div className="text-3xl mb-3 opacity-40">💭</div>
      <p className="text-terminal-dim text-sm font-mono">
        Agent thinking steps will appear here
      </p>
      <p className="text-terminal-dim/60 text-xs font-mono mt-1">
        as the agent works through your topic
      </p>
    </div>
  )
}

export function ReportEmptyState() {
  const features = [
    { icon: <FlaskConical className="w-4 h-4" />, text: 'Validates your topic first' },
    { icon: <Globe className="w-4 h-4" />, text: 'Searches up to 20 web sources' },
    { icon: <BookOpen className="w-4 h-4" />, text: 'Checks local knowledge base' },
    { icon: <FileText className="w-4 h-4" />, text: 'Generates a structured PDF report' },
  ]

  return (
    <div className="flex flex-col items-center justify-center h-full text-center px-8 py-12">
      <div className="text-5xl mb-5">📋</div>
      <h3 className="text-slate-800 font-semibold text-lg mb-2">
        Research report will appear here
      </h3>
      <p className="text-slate-500 text-sm mb-8 max-w-xs">
        Enter a topic above and click <strong>Research</strong> to generate a
        comprehensive, structured report.
      </p>
      <div className="flex flex-col gap-2 text-left">
        {features.map((f, i) => (
          <div key={i} className="flex items-center gap-2.5 text-slate-500 text-sm">
            <span className="text-indigo-400">{f.icon}</span>
            {f.text}
          </div>
        ))}
      </div>
    </div>
  )
}
