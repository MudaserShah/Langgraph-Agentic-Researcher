/**
 * HistoryList.tsx — Scrollable list of past research reports.
 *
 * Loads the history on mount (when the History tab is opened).
 * Clicking "View" loads the full report into the research panel via onViewReport.
 */

import { RefreshCw } from 'lucide-react'
import { useEffect } from 'react'
import type { FullReport } from '../../lib/types'
import { Button } from '../ui/button'
import { HistoryCard } from './HistoryCard'
import { HistoryEmpty } from './HistoryEmpty'
import { useHistory } from '../../hooks/useHistory'

interface HistoryListProps {
  onViewReport: (report: FullReport) => void
}

export function HistoryList({ onViewReport }: HistoryListProps) {
  const { reports, isLoading, error, loadHistory, viewReport, removeReport } = useHistory()

  // Load history when the component first mounts (i.e. when tab is opened)
  useEffect(() => {
    loadHistory()
  }, [loadHistory])

  const handleView = async (id: string) => {
    const report = await viewReport(id)
    if (report) {
      onViewReport(report)
    }
  }

  return (
    <div className="flex-1 overflow-y-auto">
      <div className="max-w-3xl mx-auto px-4 sm:px-6 py-6">

        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-slate-900 font-bold text-xl">Research History</h2>
            <p className="text-slate-500 text-sm mt-0.5">
              All past research reports — view, download, or delete
            </p>
          </div>
          <Button
            variant="secondary"
            size="sm"
            onClick={loadHistory}
            isLoading={isLoading}
          >
            <RefreshCw className="w-3.5 h-3.5" />
            Refresh
          </Button>
        </div>

        {/* Error message */}
        {error && (
          <div className="mb-4 p-3 rounded-lg bg-red-50 border border-red-200 text-red-700 text-sm">
            {error}
          </div>
        )}

        {/* Loading state */}
        {isLoading && reports.length === 0 && (
          <div className="flex justify-center py-16">
            <div className="flex items-center gap-2 text-slate-400 text-sm">
              <RefreshCw className="w-4 h-4 animate-spin" />
              Loading history...
            </div>
          </div>
        )}

        {/* Empty state */}
        {!isLoading && reports.length === 0 && !error && <HistoryEmpty />}

        {/* Report cards */}
        {reports.length > 0 && (
          <div className="flex flex-col gap-3">
            {reports.map(item => (
              <HistoryCard
                key={item.id}
                item={item}
                onView={handleView}
                onDelete={removeReport}
              />
            ))}
          </div>
        )}

      </div>
    </div>
  )
}
