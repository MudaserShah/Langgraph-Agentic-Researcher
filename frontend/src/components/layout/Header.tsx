/**
 * Header.tsx — Application header with logo and tab navigation.
 *
 * The gradient background (dark slate → indigo) gives a professional SaaS look.
 * The tab bar switches between the Research and History views.
 */

import { FlaskConical, History, Search } from 'lucide-react'
import { cn } from '../../lib/utils'

type Tab = 'research' | 'history'

interface HeaderProps {
  activeTab: Tab
  onTabChange: (tab: Tab) => void
}

export function Header({ activeTab, onTabChange }: HeaderProps) {
  return (
    <header className="bg-gradient-to-r from-slate-900 via-slate-800 to-indigo-950 shadow-lg">
      <div className="max-w-screen-2xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between gap-4">

        {/* ── Logo + title ─────────────────────────────────────────── */}
        <div className="flex items-center gap-3 min-w-0">
          <div className="flex-shrink-0 p-2 bg-indigo-500/20 rounded-lg border border-indigo-500/30">
            <FlaskConical className="w-5 h-5 text-indigo-300" />
          </div>
          <div className="min-w-0">
            <h1 className="text-white font-bold text-base leading-tight truncate">
              Agentic Researcher
            </h1>
            <p className="text-indigo-300/70 text-xs truncate hidden sm:block">
              Lecture 19 · LangGraph · Web Search · PDF Reports
            </p>
          </div>
        </div>

        {/* ── Tab navigation ───────────────────────────────────────── */}
        <nav className="flex items-center gap-1 bg-white/10 rounded-lg p-1 backdrop-blur-sm">
          <TabButton
            tab="research"
            activeTab={activeTab}
            onClick={onTabChange}
            icon={<Search className="w-3.5 h-3.5" />}
            label="Research"
          />
          <TabButton
            tab="history"
            activeTab={activeTab}
            onClick={onTabChange}
            icon={<History className="w-3.5 h-3.5" />}
            label="History"
          />
        </nav>

      </div>
    </header>
  )
}

// ── Internal TabButton component ──────────────────────────────────────────────

interface TabButtonProps {
  tab: Tab
  activeTab: Tab
  onClick: (tab: Tab) => void
  icon: React.ReactNode
  label: string
}

function TabButton({ tab, activeTab, onClick, icon, label }: TabButtonProps) {
  const isActive = tab === activeTab

  return (
    <button
      onClick={() => onClick(tab)}
      className={cn(
        'flex items-center gap-1.5 px-3.5 py-1.5 rounded-md text-sm font-medium',
        'transition-all duration-150 focus:outline-none',
        isActive
          ? 'bg-white text-slate-900 shadow-sm'
          : 'text-white/70 hover:text-white hover:bg-white/10',
      )}
    >
      {icon}
      {label}
    </button>
  )
}
