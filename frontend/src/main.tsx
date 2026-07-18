/**
 * main.tsx — React application entry point.
 *
 * This file mounts the React app onto the DOM element with id="root"
 * (defined in index.html). It's the equivalent of the <script> tag
 * at the bottom of a plain HTML page — just the starting point.
 *
 * StrictMode: A development tool that highlights potential problems.
 * It runs each component's render function TWICE to help catch bugs
 * caused by side effects. Has no effect in production builds.
 */

import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import { ErrorBoundary } from './components/ErrorBoundary'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <ErrorBoundary>
      <App />
    </ErrorBoundary>
  </React.StrictMode>
)
