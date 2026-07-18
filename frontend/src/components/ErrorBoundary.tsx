/**
 * ErrorBoundary.tsx — Catches React rendering errors so the app doesn't go blank.
 *
 * Without this, any thrown error inside a component causes React to unmount
 * the ENTIRE app and show a blank/black screen. With this boundary, only
 * the crashed component's subtree is replaced with the fallback UI.
 *
 * This is a class component because React error boundaries must be class components
 * (there is no hook equivalent for componentDidCatch).
 */

import { Component, type ErrorInfo, type ReactNode } from 'react'

interface Props {
  children: ReactNode
  fallback?: ReactNode
}

interface State {
  hasError: boolean
  error: Error | null
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error('ErrorBoundary caught:', error, info.componentStack)
  }

  render() {
    if (this.state.hasError) {
      return this.props.fallback ?? (
        <div className="flex flex-col items-center justify-center h-full p-8 text-center">
          <div className="text-4xl mb-4">⚠️</div>
          <h2 className="text-slate-800 font-semibold text-lg mb-2">
            Something went wrong rendering this panel
          </h2>
          <p className="text-slate-500 text-sm mb-4 max-w-md font-mono">
            {this.state.error?.message}
          </p>
          <button
            onClick={() => this.setState({ hasError: false, error: null })}
            className="px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm hover:bg-indigo-700"
          >
            Try again
          </button>
        </div>
      )
    }
    return this.props.children
  }
}
