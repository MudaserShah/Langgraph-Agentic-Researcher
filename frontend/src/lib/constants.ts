/**
 * constants.ts — Static configuration values shared across components.
 *
 * NODE_CONFIG maps each LangGraph node name to its display properties:
 *   color  — the left-border colour in the thinking panel
 *   label  — the short name shown in the node header
 *   Icon   — the Lucide React icon component
 *
 * These colours match the original app.js NODE_CONFIG.
 */

import {
  BookOpen,
  Brain,
  Globe,
  Map,
  PenLine,
  ShieldCheck,
} from 'lucide-react'
import type { NodeConfig, NodeName } from './types'

export const NODE_CONFIG: Record<NodeName, NodeConfig> = {
  validate_topic: {
    color: '#7c3aed',   // purple
    label: 'Validate',
    Icon: ShieldCheck,
  },
  analyze_query: {
    color: '#2563eb',   // blue
    label: 'Analyze',
    Icon: Brain,
  },
  decide_search_strategy: {
    color: '#0891b2',   // cyan
    label: 'Strategy',
    Icon: Map,
  },
  web_search: {
    color: '#059669',   // green
    label: 'Web Search',
    Icon: Globe,
  },
  kb_search: {
    color: '#d97706',   // amber
    label: 'Knowledge Base',
    Icon: BookOpen,
  },
  synthesize: {
    color: '#dc2626',   // red
    label: 'Synthesize',
    Icon: PenLine,
  },
}
