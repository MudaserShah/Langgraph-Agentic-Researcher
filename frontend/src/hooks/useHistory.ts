/**
 * useHistory.ts — Custom React hook for research history management.
 *
 * Handles: loading the list, viewing a full report, and deleting entries.
 * All state (reports, loading, error) lives here, not in the component.
 */

import { useCallback, useState } from 'react'
import { deleteReport, getFullReport, getHistory } from '../lib/api'
import type { FullReport, HistoryItem } from '../lib/types'

export interface UseHistoryReturn {
  reports: HistoryItem[]
  isLoading: boolean
  error: string | null
  loadHistory: () => Promise<void>
  viewReport: (id: string) => Promise<FullReport | null>
  removeReport: (id: string) => Promise<void>
}

export function useHistory(): UseHistoryReturn {
  const [reports, setReports] = useState<HistoryItem[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const loadHistory = useCallback(async () => {
    setIsLoading(true)
    setError(null)
    try {
      const data = await getHistory()
      setReports(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load history')
    } finally {
      setIsLoading(false)
    }
  }, [])

  const viewReport = useCallback(async (id: string): Promise<FullReport | null> => {
    try {
      return await getFullReport(id)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load report')
      return null
    }
  }, [])

  const removeReport = useCallback(async (id: string) => {
    try {
      await deleteReport(id)
      // Optimistic update — remove from local state immediately
      setReports(prev => prev.filter(r => r.id !== id))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete report')
    }
  }, [])

  return { reports, isLoading, error, loadHistory, viewReport, removeReport }
}
