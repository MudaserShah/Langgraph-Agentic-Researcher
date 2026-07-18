/**
 * ReportActions.tsx — Download PDF and Print buttons for the report.
 */

import { Download, Printer } from 'lucide-react'
import { useState } from 'react'
import { downloadPdf } from '../../lib/api'
import { Button } from '../ui/button'

interface ReportActionsProps {
  reportId: string
  topic: string
}

export function ReportActions({ reportId, topic }: ReportActionsProps) {
  const [isDownloading, setIsDownloading] = useState(false)

  const handleDownload = async () => {
    setIsDownloading(true)
    try {
      await downloadPdf(reportId, topic)
    } catch (err) {
      console.error('PDF download failed:', err)
      alert('PDF download failed. Please try again.')
    } finally {
      setIsDownloading(false)
    }
  }

  return (
    <div className="flex items-center gap-2">
      <Button
        variant="primary"
        size="sm"
        onClick={handleDownload}
        isLoading={isDownloading}
      >
        <Download className="w-3.5 h-3.5" />
        {isDownloading ? 'Generating...' : 'Download PDF'}
      </Button>
      <Button
        variant="ghost"
        size="sm"
        onClick={() => window.print()}
      >
        <Printer className="w-3.5 h-3.5" />
        Print
      </Button>
    </div>
  )
}
