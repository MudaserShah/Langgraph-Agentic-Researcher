/**
 * api.ts — All HTTP calls to the backend.
 *
 * KEY RULE: Components never call fetch() directly. All API calls go through
 * this file. This keeps the API surface in one place — if the backend URL
 * or a request format changes, you fix it here, not in 10 components.
 *
 * SSE STREAMING:
 *   The /research endpoint uses Server-Sent Events (SSE).
 *   Normally you'd use the browser's EventSource API for SSE, but EventSource
 *   only supports GET requests. Our endpoint is POST (we need to send the topic).
 *   So we use fetch() + response.body.getReader() instead — same protocol,
 *   just a different client that supports POST.
 *
 *   Stream format:
 *     data: {"event": "start", "message": "..."}\n\n
 *     data: {"event": "thinking", "node": "...", "message": "..."}\n\n
 *     data: [DONE]\n\n
 *
 *   We accumulate chunks in a buffer and split on "\n\n" to parse events.
 */

import type { FullReport, HistoryItem, SSEEvent } from './types'

// Read the backend URL from the Vite environment variable.
// Set in frontend/.env as VITE_API_BASE=http://localhost:8002
// The ?? fallback handles the case where the .env file is missing.
const API_BASE = import.meta.env.VITE_API_BASE ?? 'http://localhost:8002'


// ── Research (SSE streaming) ──────────────────────────────────────────────────

/**
 * Open a streaming research session.
 *
 * @param topic         The research topic the user typed
 * @param useWebSearch  null = let agent decide; true = force web search
 * @param onEvent       Callback called for each SSE event as it arrives
 * @param signal        AbortSignal — call controller.abort() to cancel
 *
 * The function reads the stream until [DONE] or the signal is aborted.
 * Throws if the fetch fails or the stream errors.
 */
export async function streamResearch(
  topic: string,
  useWebSearch: boolean | null,
  onEvent: (event: SSEEvent) => void,
  signal: AbortSignal,
): Promise<void> {
  const response = await fetch(`${API_BASE}/research`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ topic, use_web_search: useWebSearch }),
    signal,
  })

  if (!response.ok) {
    throw new Error(`Research request failed: ${response.status} ${response.statusText}`)
  }

  if (!response.body) {
    throw new Error('Response body is null — browser does not support streaming')
  }

  // ReadableStream reader — reads chunks of bytes as they arrive from the server
  const reader = response.body.getReader()
  const decoder = new TextDecoder()

  // Buffer accumulates partial chunks between reads.
  // SSE events end with "\n\n" — we split on that to extract complete events.
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    // Decode the bytes to a string (stream: true handles multi-byte characters
    // that might be split across chunks)
    buffer += decoder.decode(value, { stream: true })

    // Split on double newline — each complete SSE event ends with \n\n
    const parts = buffer.split('\n\n')

    // The last element might be an incomplete event — keep it in the buffer
    buffer = parts.pop() ?? ''

    for (const part of parts) {
      const trimmed = part.trim()

      // SSE events start with "data: "
      if (!trimmed.startsWith('data: ')) continue

      const raw = trimmed.slice(6)  // Remove the "data: " prefix

      // [DONE] is the sentinel that signals the stream is finished
      if (raw === '[DONE]') return

      // Parse the JSON payload and call the callback
      try {
        onEvent(JSON.parse(raw) as SSEEvent)
      } catch {
        // Malformed JSON — skip silently (shouldn't happen in normal operation)
        console.warn('Failed to parse SSE event:', raw)
      }
    }
  }
}


// ── History ───────────────────────────────────────────────────────────────────

/**
 * Fetch the list of all past research reports (summaries only).
 */
export async function getHistory(): Promise<HistoryItem[]> {
  const response = await fetch(`${API_BASE}/history`)
  if (!response.ok) throw new Error(`Failed to load history: ${response.status}`)
  const data = await response.json()
  return data.reports as HistoryItem[]
}

/**
 * Fetch the full details of one past research report.
 */
export async function getFullReport(reportId: string): Promise<FullReport> {
  const response = await fetch(`${API_BASE}/history/${reportId}`)
  if (!response.ok) throw new Error(`Failed to load report: ${response.status}`)
  return response.json() as Promise<FullReport>
}

/**
 * Delete a research report by ID.
 */
export async function deleteReport(reportId: string): Promise<void> {
  const response = await fetch(`${API_BASE}/history/${reportId}`, { method: 'DELETE' })
  if (!response.ok) throw new Error(`Failed to delete report: ${response.status}`)
}

/**
 * Download a research report as a PDF file.
 *
 * HOW IT WORKS:
 *   1. Fetch the PDF bytes from the backend
 *   2. Create a Blob (in-memory binary data) from the bytes
 *   3. Create a temporary object URL pointing to the Blob
 *   4. Simulate a link click to trigger the browser's "Save As" dialog
 *   5. Clean up the object URL after download
 */
export async function downloadPdf(reportId: string, topic: string): Promise<void> {
  const response = await fetch(`${API_BASE}/history/${reportId}/pdf`)
  if (!response.ok) throw new Error(`PDF generation failed: ${response.status}`)

  const blob = await response.blob()
  const url = URL.createObjectURL(blob)

  // Create a temporary <a> element to trigger the download
  const a = document.createElement('a')
  a.href = url
  // Sanitize topic for use in filename
  const safeTopic = topic.replace(/[^a-zA-Z0-9\s_-]/g, '_').slice(0, 30).trim()
  a.download = `research_${safeTopic}_${reportId}.pdf`

  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)

  // Free the memory used by the Blob URL
  URL.revokeObjectURL(url)
}
