/**
 * App.tsx — Root component. Manages tab state and wires all pieces together.
 *
 * LAYOUT OVERVIEW:
 *
 *   ┌─────────────────────────────────────────┐
 *   │  Header (gradient + tab navigation)     │
 *   ├─────────────────────────────────────────┤
 *   │  ResearchInput (topic + toggle + button)│  ← shown on Research tab
 *   ├──────────────────┬──────────────────────┤
 *   │  ThinkingPanel   │  ReportPanel         │  ← shown on Research tab
 *   │  (38% width)     │  (62% width)         │
 *   │  Dark terminal   │  White, prose        │
 *   └──────────────────┴──────────────────────┘
 *
 *   OR on History tab:
 *
 *   ┌─────────────────────────────────────────┐
 *   │  Header                                 │
 *   ├─────────────────────────────────────────┤
 *   │  HistoryList (full width, centered)     │
 *   └─────────────────────────────────────────┘
 *
 * STATE:
 *   - activeTab: 'research' | 'history'
 *   - useResearch hook: all SSE streaming state
 *   - When "View" is clicked in History, the full report is loaded into the
 *     Research panel and the tab switches to 'research'
 */

import { useState } from 'react'
import { Header } from './components/layout/Header'
import { ReportPanel } from './components/research/ReportPanel'
import { ResearchInput } from './components/research/ResearchInput'
import { ThinkingPanel } from './components/research/ThinkingPanel'
import { HistoryList } from './components/history/HistoryList'
import { useResearch } from './hooks/useResearch'
import type { FullReport } from './lib/types'

type Tab = 'research' | 'history'

export default function App() {
  const [activeTab, setActiveTab] = useState<Tab>('research')

  const {
    isResearching,
    thinkingSteps,
    report,
    sources,
    subQuestions,
    reportId,
    researchStats,
    error,
    startResearch,
    cancelResearch,
    clear,
  } = useResearch()

  // Track the current topic for the PDF filename
  const [currentTopic, setCurrentTopic] = useState('')

  const handleSubmit = (topic: string, useWebSearch: boolean | null) => {
    setCurrentTopic(topic)
    startResearch(topic, useWebSearch)
  }

  // When a history item is "viewed", load it into the research panel
  const handleViewHistoryReport = (fullReport: FullReport) => {
    // We don't re-run the agent — just display the stored report
    // This reuses the same panel but populates state directly
    setCurrentTopic(fullReport.topic)
    // Use a hack-free approach: we call a special path via the research hook
    // For history view, we inject the data directly into state
    // Actually, the simplest approach: switch to research tab and display inline
    handleInjectReport(fullReport)
    setActiveTab('research')
  }

  // Inject a stored report directly into the research panel
  // (bypasses the SSE stream — we already have the data)
  const [injectedReport, setInjectedReport] = useState<{
    report: string
    sources: FullReport['sources']
    subQuestions: string[]
    reportId: string
    topic: string
  } | null>(null)

  const handleInjectReport = (fullReport: FullReport) => {
    setInjectedReport({
      report: fullReport.report_md,
      sources: fullReport.sources,
      subQuestions: fullReport.sub_questions,
      reportId: fullReport.id,
      topic: fullReport.topic,
    })
  }

  // Displayed report data — either from live SSE or injected from history
  const displayReport = report ?? injectedReport?.report ?? null
  const displaySources = sources.length > 0 ? sources : (injectedReport?.sources ?? [])
  const displaySubQuestions = subQuestions.length > 0 ? subQuestions : (injectedReport?.subQuestions ?? [])
  const displayReportId = reportId ?? injectedReport?.reportId ?? null
  const displayTopic = currentTopic || injectedReport?.topic || ''

  const handleClear = () => {
    clear()
    setInjectedReport(null)
    setCurrentTopic('')
  }

  return (
    // Full-height flex column — header + content fill the viewport
    <div className="h-screen flex flex-col bg-slate-50 overflow-hidden">

      {/* ── Fixed header ─────────────────────────────────────────── */}
      <Header activeTab={activeTab} onTabChange={setActiveTab} />

      {/* ── Tab content ──────────────────────────────────────────── */}

      {/* RESEARCH TAB */}
      {activeTab === 'research' && (
        <div className="flex-1 flex flex-col min-h-0">
          {/* Input bar — fixed height */}
          <ResearchInput
            isResearching={isResearching}
            onSubmit={handleSubmit}
            onClear={handleClear}
          />

          {/* Error banner */}
          {error && (
            <div className="mx-4 mt-2 px-4 py-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm flex-shrink-0">
              <span className="font-semibold">Error: </span>{error}
            </div>
          )}

          {/* Split panel layout — fills remaining height */}
          <div className="flex-1 flex min-h-0 gap-0 p-3 gap-3">

            {/* Left: Thinking panel (38%) */}
            <div className="w-[38%] min-w-0 flex flex-col">
              <ThinkingPanel steps={thinkingSteps} isLive={isResearching} />
            </div>

            {/* Right: Report panel (62%) */}
            <div className="flex-1 min-w-0 flex flex-col">
              <ReportPanel
                report={displayReport}
                sources={displaySources}
                subQuestions={displaySubQuestions}
                reportId={displayReportId}
                researchStats={researchStats}
                topic={displayTopic}
                isResearching={isResearching}
              />
            </div>

          </div>
        </div>
      )}

      {/* HISTORY TAB */}
      {activeTab === 'history' && (
        <div className="flex-1 min-h-0 flex flex-col">
          <HistoryList onViewReport={handleViewHistoryReport} />
        </div>
      )}

    </div>
  )
}
