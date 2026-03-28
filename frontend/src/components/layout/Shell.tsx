import { Outlet, useLocation } from 'react-router-dom'
import { Sidebar } from './Sidebar'
import { TopBar } from './TopBar'

const PAGE_TITLES: Record<string, string> = {
  '/':             'Overview',
  '/upload':       'Upload & Parse',
  '/explorer':     'Log Explorer',
  '/analytics':    'Analytics',
  '/query':        'Natural Language Query',
  '/summary':      'Summary Report',
  '/architecture': 'Architecture',
}

export function Shell() {
  const { pathname } = useLocation()
  const title = PAGE_TITLES[pathname] ?? 'Smart Log Parser'
  return (
    <div className="flex h-screen bg-bg-base overflow-hidden">
      <Sidebar />
      <div className="flex flex-col flex-1 min-w-0">
        <TopBar title={title} />
        <main className="flex-1 overflow-y-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
