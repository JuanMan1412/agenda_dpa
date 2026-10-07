import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Toaster } from 'sonner'
import './index.css'
import App from './App.jsx'
import { PermissionsProvider } from './contexts/PermissionsContext'

const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false, staleTime: 0 } } });
createRoot(document.getElementById('root')).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter><PermissionsProvider><App /></PermissionsProvider></BrowserRouter>
      <Toaster position="top-right" richColors closeButton duration={6000} toastOptions={{ style: { fontFamily: 'inherit' } }} />
    </QueryClientProvider>
  </StrictMode>,
)
