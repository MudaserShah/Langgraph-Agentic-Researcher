/**
 * ReportPanel.tsx — Right panel displaying the rendered research report.
 *
 * Uses react-markdown + remark-gfm to render the markdown report as HTML.
 * The `prose` class from @tailwindcss/typography styles it beautifully.
 *
 * This replaces the hand-rolled convertMarkdownToHtml() function from app.js
 * with a proper, full-featured markdown parser.
 *
 * WHAT IS react-markdown?
 *   react-markdown converts markdown text → React components.
 *   It handles headings, lists, bold, italic, links, code blocks, etc.
 *   remark-gfm adds GitHub Flavored Markdown support (tables, strikethrough, etc.)
 */

import { Loader2, FileText } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import type { ResearchStats, Source } from '../../lib/types'
import { ErrorBoundary } from '../ErrorBoundary'
import { ReportEmptyState } from './EmptyState'
import { ReportActions } from './ReportActions'
import { ResearchSummary } from './ResearchSummary'
import { SourceCard } from './SourceCard'
import { SubQuestions } from './SubQuestions'

interface ReportPanelProps {
  report: string | null
  sources: Source[]
  subQuestions: string[]
  reportId: string | null
  researchStats: ResearchStats | null
  topic: string
  isResearching: boolean
}

export function ReportPanel({
  report,
  sources,
  subQuestions,
  reportId,
  researchStats,
  topic,
  isResearching,
}: ReportPanelProps) {

  return (
    <div className="flex flex-col h-full bg-white border border-slate-200 rounded-xl overflow-hidden">

      {/* ── Panel header ─────────────────────────────────────────── */}
      <div className="flex items-center justify-between px-5 py-3 border-b border-slate-100 bg-white flex-shrink-0">
        <div className="flex items-center gap-2">
          <FileText className="w-4 h-4 text-slate-400" />
          <span className="text-sm font-semibold text-slate-700">Research Report</span>
          {/* Spinner while research is running */}
          {isResearching && (
            <span className="flex items-center gap-1.5 text-xs text-indigo-500 font-medium ml-1">
              <Loader2 className="w-3 h-3 animate-spin" />
              Generating...
            </span>
          )}
        </div>

        {/* PDF + Print buttons — only shown when a report exists */}
        {report && reportId && (
          <ReportActions reportId={reportId} topic={topic} />
        )}
      </div>

      {/* ── Report content ────────────────────────────────────────── */}
      <div className="flex-1 overflow-y-auto">
        {!report ? (
          /* Show a "working" placeholder while agent is running */
          isResearching ? (
            <div className="flex flex-col items-center justify-center h-full text-center px-8 py-12">
              <Loader2 className="w-10 h-10 text-indigo-400 animate-spin mb-4" />
              <p className="text-slate-600 font-medium mb-1">Agent is researching…</p>
              <p className="text-slate-400 text-sm">
                Watch the thinking panel on the left for live progress
              </p>
            </div>
          ) : (
            <ReportEmptyState />
          )
        ) : (
          <div className="px-8 py-6">
            {/* Research summary audit card (from "summary" SSE event) */}
            {researchStats && <ResearchSummary stats={researchStats} />}

            {/* Sub-questions pills */}
            <SubQuestions questions={subQuestions} />

            {/* Markdown report wrapped in ErrorBoundary so a crash here
                doesn't blank the whole screen */}
            <ErrorBoundary>
              <div className="prose-report">
                <ReactMarkdown
                  remarkPlugins={[remarkGfm]}
                  components={{
                    // Hide the "Sources" heading — we render them as cards below
                    h2: ({ children, ...props }) => {
                      const text = typeof children === 'string'
                        ? children
                        : Array.isArray(children)
                          ? children.filter(c => typeof c === 'string').join('')
                          : ''
                      if (text.toLowerCase().includes('sources') || text.toLowerCase().includes('references')) {
                        return null
                      }
                      return <h2 {...props}>{children}</h2>
                    },
                    // Open links in new tab safely
                    a: ({ href, children }) => (
                      <a href={href} target="_blank" rel="noopener noreferrer">
                        {children}
                      </a>
                    ),
                  }}
                >
                  {stripSourcesSection(report)}
                </ReactMarkdown>
              </div>
            </ErrorBoundary>

            {/* Sources rendered as structured cards */}
            {sources.length > 0 && (
              <div className="mt-8 pt-6 border-t border-slate-200">
                <h2 className="text-base font-semibold text-slate-800 mb-4 flex items-center gap-2">
                  <span className="text-slate-400">📚</span>
                  Sources ({sources.length})
                </h2>
                <div className="flex flex-col gap-2">
                  {sources.map((source, i) => (
                    <SourceCard key={i} source={source} index={i} />
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

/**
 * Remove the Sources/References section from the markdown before rendering.
 * We render sources separately as structured SourceCard components below.
 */
function stripSourcesSection(markdown: string): string {
  const lines = markdown.split('\n')
  const sourcesIdx = lines.findIndex(line =>
    /^## (sources|references|📚 sources)/i.test(line.trim())
  )
  if (sourcesIdx === -1) return markdown
  return lines.slice(0, sourcesIdx).join('\n')
}
