/**
 * HistoryEmpty.tsx — Placeholder shown when no research history exists yet.
 */

export function HistoryEmpty() {
  return (
    <div className="flex flex-col items-center justify-center py-24 text-center">
      <div className="text-5xl mb-4">📭</div>
      <h3 className="text-slate-700 font-semibold text-lg mb-2">No research history yet</h3>
      <p className="text-slate-400 text-sm max-w-xs">
        Complete a research session on the Research tab and your reports will appear here.
      </p>
    </div>
  )
}
