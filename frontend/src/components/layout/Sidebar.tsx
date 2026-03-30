import { NavLink } from 'react-router-dom'
import {
  LayoutDashboard, Upload, Table, BarChart2,
  MessageSquare, FileText, Cpu,
} from 'lucide-react'
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip'

const NAV = [
  { to: '/',             icon: LayoutDashboard, label: 'Overview'     },
  { to: '/upload',       icon: Upload,          label: 'Upload'       },
  { to: '/explorer',     icon: Table,           label: 'Explorer'     },
  { to: '/analytics',    icon: BarChart2,        label: 'Analytics'   },
  { to: '/query',        icon: MessageSquare,   label: 'NL Query'     },
  { to: '/summary',      icon: FileText,        label: 'Summary'      },
  { to: '/architecture', icon: Cpu,             label: 'Architecture' },
]

export function Sidebar() {
  return (
    <TooltipProvider delayDuration={200}>
      <nav className="w-20 shrink-0 bg-[#0d1017] border-r border-border flex flex-col items-center py-5 gap-3">
        {/* Logo mark */}
        <div className="w-10 h-10 rounded-lg bg-accent-blue flex items-center justify-center mb-5 shadow-[0_0_16px_rgba(59,130,246,0.4)]">
          <span className="text-white text-sm font-bold tracking-tight">SL</span>
        </div>
        {NAV.map(({ to, icon: Icon, label }) => (
          <Tooltip key={to}>
            <TooltipTrigger asChild>
              <NavLink
                to={to}
                end={to === '/'}
                className={({ isActive }) =>
                  `w-full h-11 px-2 rounded-lg flex items-center justify-center transition-all duration-200 ${
                    isActive
                      ? 'bg-accent-blue/20 text-accent-blue ring-1 ring-accent-blue/30 shadow-[0_0_14px_rgba(59,130,246,0.3)]'
                      : 'text-text-muted hover:text-text-primary hover:bg-bg-raised transition-all duration-200'
                  }`
                }
              >
                <Icon className="w-6 h-6" />
              </NavLink>
            </TooltipTrigger>
            <TooltipContent side="right" className="bg-bg-raised text-text-primary border-border text-xs">
              {label}
            </TooltipContent>
          </Tooltip>
        ))}
      </nav>
    </TooltipProvider>
  )
}
