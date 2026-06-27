import React from 'react'
import ReactDOM from 'react-dom/client'
import i18n from 'i18next'
import { initReactI18next } from 'react-i18next'
import { translations } from './i18n/translations.js'
import App from './App.jsx'
import './index.css'

// ── i18next initialisation ────────────────────────────────────────────────────
i18n
  .use(initReactI18next)
  .init({
    resources: translations,
    lng: localStorage.getItem('kaveri-lang') || 'en',
    fallbackLng: 'en',
    interpolation: {
      escapeValue: false, // React already escapes
    },
  })

// ── Mount ─────────────────────────────────────────────────────────────────────
ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
)
