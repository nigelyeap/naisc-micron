import { createBrowserRouter, RouterProvider } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Shell } from '@/components/layout/Shell'
import { OverviewPage }      from '@/pages/OverviewPage'
import { UploadPage }        from '@/pages/UploadPage'
import { ExplorerPage }      from '@/pages/ExplorerPage'
import { AnalyticsPage }     from '@/pages/AnalyticsPage'
import { NlQueryPage }       from '@/pages/NlQueryPage'
import { SummaryPage }       from '@/pages/SummaryPage'
import { ArchitecturePage }  from '@/pages/ArchitecturePage'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      retry: 1,
    },
  },
})

const router = createBrowserRouter([
  {
    path: '/',
    element: <Shell />,
    children: [
      { index: true,          element: <OverviewPage /> },
      { path: 'upload',       element: <UploadPage /> },
      { path: 'explorer',     element: <ExplorerPage /> },
      { path: 'analytics',    element: <AnalyticsPage /> },
      { path: 'query',        element: <NlQueryPage /> },
      { path: 'summary',      element: <SummaryPage /> },
      { path: 'architecture', element: <ArchitecturePage /> },
    ],
  },
])

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
    </QueryClientProvider>
  )
}
