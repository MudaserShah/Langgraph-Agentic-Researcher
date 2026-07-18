/**
 * useResearch.ts — Custom React hook for the research SSE streaming flow.
 *
 * WHAT IS A CUSTOM HOOK?
 *   A custom hook is a function whose name starts with "use" that calls
 *   other React hooks (useState, useRef, useCallback, etc.).
 *   It lets you extract stateful logic out of a component into a reusable function.
 *
 *   Without a hook, all of this logic would live in ResearchInput.tsx or App.tsx —
 *   making that file huge and hard to read. The hook keeps UI code (JSX) separate
 *   from logic code (state + effects).
 *
 * WHAT THIS HOOK MANAGES:
 *   - isResearching: bool — is a stream currently active?
 *   - thinkingSteps: list of steps shown in the left panel
 *   - report: final markdown report text
 *   - sources: list of web sources
 *   - subQuestions: the 3 sub-questions the agent generated
 *   - reportId: ID used for PDF download URL
 *   - researchStats: summary stats from the "summary" SSE event
 *   - error: error message if something went wrong
 *   - startResearch(): open the SSE stream
 *   - cancelResearch(): abort the stream
 *   - clear(): reset all state
 */

import { useCallback, useRef, useState } from 'react'
import { streamResearch } from '../lib/api'
import type { ResearchStats, Source, SSEEvent, ThinkingStep } from '../lib/types'

// Return type of the hook — exported so callers can type their props
export interface UseResearchReturn {
  isResearching: boolean
  thinkingSteps: ThinkingStep[]
  report: string | null
  sources: Source[]
  subQuestions: string[]
  reportId: string | null
  researchStats: ResearchStats | null
  error: string | null
  startResearch: (topic: string, useWebSearch: boolean | null) => void
  cancelResearch: () => void
  clear: () => void
}

export function useResearch(): UseResearchReturn {
  // ── State ─────────────────────────────────────────────────────────────────
  const [isResearching, setIsResearching] = useState(false)
  const [thinkingSteps, setThinkingSteps] = useState<ThinkingStep[]>([])
  const [report, setReport] = useState<string | null>(null)
  const [sources, setSources] = useState<Source[]>([])
  const [subQuestions, setSubQuestions] = useState<string[]>([])
  const [reportId, setReportId] = useState<string | null>(null)
  const [researchStats, setResearchStats] = useState<ResearchStats | null>(null)
  const [error, setError] = useState<string | null>(null)

  // ── AbortController ref ───────────────────────────────────────────────────
  // We use a ref (not state) for the controller because:
  //   1. We don't want updating it to trigger a re-render
  //   2. We need the latest value in startResearch without stale closure issues
  const abortControllerRef = useRef<AbortController | null>(null)

  // ── Step ID counter ───────────────────────────────────────────────────────
  // Each thinking step needs a unique key for React's reconciler.
  // Using a ref counter is simpler and faster than Date.now() + Math.random().
  const stepIdRef = useRef(0)

  // Helper: add a step to the thinking panel
  const addStep = useCallback((
    node: ThinkingStep['node'],
    message: string,
    isHeader: boolean,
  ) => {
    stepIdRef.current += 1
    const step: ThinkingStep = {
      id: `step-${stepIdRef.current}`,
      node,
      message,
      isHeader,
    }
    setThinkingSteps(prev => [...prev, step])
  }, [])

  // ── SSE event handler ─────────────────────────────────────────────────────
  const handleEvent = useCallback((event: SSEEvent) => {
    switch (event.event) {
      case 'start':
        // Server acknowledged the request — nothing to render yet
        break

      case 'node_start':
        // A new agent node started — add a header row in the thinking panel
        addStep(event.node, event.display, true)
        break

      case 'thinking':
        // A detail step from inside a node — add an indented row
        addStep(event.node, event.message, false)
        break

      case 'complete':
        // Agent finished — update report, sources, sub-questions, report ID
        setReport(event.report)
        setSources(event.sources)
        setSubQuestions(event.sub_questions)
        setReportId(event.report_id)
        break

      case 'summary':
        // Statistics summary of the completed research session
        setResearchStats(event.stats)
        break

      case 'error':
        setError(event.message)
        break
    }
  }, [addStep])

  // ── startResearch ─────────────────────────────────────────────────────────
  const startResearch = useCallback((topic: string, useWebSearch: boolean | null) => {
    // Cancel any in-progress stream before starting a new one
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
    }

    // Create a fresh AbortController for this stream
    const controller = new AbortController()
    abortControllerRef.current = controller

    // Reset all state for the new session
    setIsResearching(true)
    setThinkingSteps([])
    setReport(null)
    setSources([])
    setSubQuestions([])
    setReportId(null)
    setResearchStats(null)
    setError(null)
    stepIdRef.current = 0

    // Start the stream (async — runs in the background)
    streamResearch(topic, useWebSearch, handleEvent, controller.signal)
      .catch(err => {
        // AbortError is expected when cancelResearch() is called — don't show as error
        if (err.name !== 'AbortError') {
          setError(err.message ?? 'An unknown error occurred')
        }
      })
      .finally(() => {
        setIsResearching(false)
      })
  }, [handleEvent])

  // ── cancelResearch ────────────────────────────────────────────────────────
  const cancelResearch = useCallback(() => {
    abortControllerRef.current?.abort()
    setIsResearching(false)
  }, [])

  // ── clear ─────────────────────────────────────────────────────────────────
  const clear = useCallback(() => {
    cancelResearch()
    setThinkingSteps([])
    setReport(null)
    setSources([])
    setSubQuestions([])
    setReportId(null)
    setResearchStats(null)
    setError(null)
    stepIdRef.current = 0
  }, [cancelResearch])

  return {
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
  }
}
