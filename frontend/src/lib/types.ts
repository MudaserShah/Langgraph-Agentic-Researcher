/**
 * types.ts — TypeScript interfaces for all data used in the app.
 *
 * These mirror the Pydantic models in backend/app/models.py.
 * When the backend returns JSON, these types tell TypeScript what shape to expect.
 *
 * WHY TYPE EVERYTHING?
 *   TypeScript catches bugs at compile time instead of runtime.
 *   If the backend changes a field name, TypeScript will show a red squiggle
 *   everywhere that field is used — instead of a mysterious undefined at runtime.
 */

import { LucideIcon } from 'lucide-react'

// ── Agent node names ──────────────────────────────────────────────────────────
// Must match the node names in backend/app/agent.py's workflow.add_node() calls.

export type NodeName =
  | 'validate_topic'
  | 'analyze_query'
  | 'decide_search_strategy'
  | 'web_search'
  | 'kb_search'
  | 'synthesize'


// ── Thinking step (frontend-only) ─────────────────────────────────────────────
// Created by useResearch.ts when a thinking/node_start SSE event arrives.

export interface ThinkingStep {
  id: string         // Unique key for React (e.g. "web_search-1713123456789")
  node: NodeName     // Which node emitted this step
  message: string    // The text content
  isHeader: boolean  // true = node header row; false = detail/thinking row
}

// ── Research stats (from "summary" SSE event) ─────────────────────────────────
export interface ResearchStats {
  topic: string
  sub_questions: string[]
  urls_searched: number
  kb_searched: boolean
  strategy: 'web_only' | 'both'
}

// ── Sources ───────────────────────────────────────────────────────────────────
// Mirrors backend/app/models.py Source

export interface Source {
  title: string
  url: string
  content_preview: string
}

// ── History ───────────────────────────────────────────────────────────────────
// Mirrors backend/app/models.py HistoryItem and HistoryListResponse

export interface HistoryItem {
  id: string
  topic: string
  url_count: number
  created_at: string
}

export interface FullReport extends HistoryItem {
  report_md: string
  sources: Source[]
  sub_questions: string[]
}

// ── SSE event types ───────────────────────────────────────────────────────────
// These match the dict shapes emitted by sse_event() in backend/app/api.py.
// Using a discriminated union (| type) so TypeScript can narrow the type
// based on the "event" field.

export type SSEEvent =
  | { event: 'start';      message: string }
  | { event: 'node_start'; node: NodeName; display: string; message: string }
  | { event: 'thinking';   node: NodeName; message: string }
  | { event: 'complete';   report: string; sources: Source[]; sub_questions: string[]; report_id: string }
  | { event: 'summary';    stats: ResearchStats }
  | { event: 'error';      message: string }


// ── Node config ───────────────────────────────────────────────────────────────
// UI display config for each agent node.
// Imported in ThinkingStep and ThinkingPanel to colour-code the steps.

export interface NodeConfig {
  color: string      // Hex colour for the left border + icon
  label: string      // Short human-readable label
  Icon: LucideIcon   // Lucide icon component
}
