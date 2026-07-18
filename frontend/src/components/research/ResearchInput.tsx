/**
 * ResearchInput.tsx — Topic input bar at the top of the research view.
 *
 * Contains:
 *   - Text input for the research topic
 *   - "Force web search" toggle switch
 *   - Research button (with loading spinner while running)
 *   - Clear button
 *
 * The Enter key also submits (same UX as a search bar).
 */

import { Loader2, Search, X } from 'lucide-react'
import { useState } from 'react'
import { Button } from '../ui/button'
import { Input } from '../ui/input'
import { Switch } from '../ui/switch'

interface ResearchInputProps {
  isResearching: boolean
  onSubmit: (topic: string, useWebSearch: boolean | null) => void
  onClear: () => void
}

export function ResearchInput({ isResearching, onSubmit, onClear }: ResearchInputProps) {
  const [topic, setTopic] = useState('')
  const [forceWebSearch, setForceWebSearch] = useState(true)

  const handleSubmit = () => {
    const trimmed = topic.trim()
    if (!trimmed || isResearching) return
    // null = let agent decide; true = force web search
    onSubmit(trimmed, forceWebSearch ? true : null)
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') handleSubmit()
  }

  const handleClear = () => {
    setTopic('')
    onClear()
  }

  return (
    <div className="px-4 py-3 bg-white border-b border-slate-200 flex-shrink-0">
      <div className="max-w-screen-2xl mx-auto flex items-center gap-3">

        {/* Topic text input */}
        <div className="flex-1 relative">
          <Input
            value={topic}
            onChange={e => setTopic(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Enter a research topic... e.g. 'Impact of AI on healthcare in 2025'"
            disabled={isResearching}
            className="pr-8"
          />
          {/* Clear X button inside input */}
          {topic && !isResearching && (
            <button
              onClick={() => setTopic('')}
              className="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
            >
              <X className="w-4 h-4" />
            </button>
          )}
        </div>

        {/* Force web search toggle */}
        <Switch
          id="force-web-search"
          checked={forceWebSearch}
          onCheckedChange={setForceWebSearch}
          label="Force web search"
          disabled={isResearching}
        />

        {/* Research / Stop button */}
        <Button
          variant="primary"
          size="md"
          onClick={isResearching ? onClear : handleSubmit}
          disabled={!isResearching && !topic.trim()}
          className="min-w-[120px]"
        >
          {isResearching ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              Researching...
            </>
          ) : (
            <>
              <Search className="w-4 h-4" />
              Research
            </>
          )}
        </Button>

        {/* Clear button — only shown when not researching */}
        {!isResearching && (
          <Button variant="ghost" size="md" onClick={handleClear}>
            Clear
          </Button>
        )}

      </div>
    </div>
  )
}
