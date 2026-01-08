import { NavLink } from 'react-router-dom';
import {
    LayoutDashboard,
    Brain,
    Wallet,
    LineChart,
    History,
    GitBranch,
    Bot
} from 'lucide-react';

const navItems = [
    { path: '/', label: 'Overview', icon: LayoutDashboard },
    { path: '/thinking', label: 'AI Thinking', icon: Brain },
    { path: '/portfolio', label: 'Portfolio', icon: Wallet },
    { path: '/market', label: 'Market', icon: LineChart },
    { path: '/trades', label: 'Trade History', icon: History },
    { path: '/architecture', label: 'Architecture', icon: GitBranch },
];

interface SidebarProps {
    lastUpdated?: string;
}

export function Sidebar({ lastUpdated }: SidebarProps) {
    return (
        <aside className="fixed left-0 top-0 h-screen w-64 bg-[var(--color-bg-secondary)] border-r border-[var(--color-border-primary)] flex flex-col z-50">
            {/* Logo */}
            <div className="p-6 border-b border-[var(--color-border-primary)]">
                <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-[var(--color-accent-primary)] to-[var(--color-accent-secondary)] flex items-center justify-center">
                        <Bot className="w-6 h-6 text-white" />
                    </div>
                    <div>
                        <h1 className="text-lg font-bold text-[var(--color-text-primary)]">LLM Arena</h1>
                        <p className="text-xs text-[var(--color-text-muted)]">AI Trading Dashboard</p>
                    </div>
                </div>
            </div>

            {/* Navigation */}
            <nav className="flex-1 p-4 space-y-1">
                {navItems.map((item) => (
                    <NavLink
                        key={item.path}
                        to={item.path}
                        className={({ isActive }) =>
                            `sidebar-link ${isActive ? 'sidebar-link-active' : ''}`
                        }
                    >
                        <item.icon className="w-5 h-5" />
                        <span className="text-sm font-medium">{item.label}</span>
                    </NavLink>
                ))}
            </nav>

            {/* Status Footer */}
            <div className="p-4 border-t border-[var(--color-border-primary)]">
                <div className="flex items-center gap-2 mb-2">
                    <span className="status-dot status-dot-live" />
                    <span className="text-xs text-[var(--color-text-secondary)]">System Active</span>
                </div>
                {lastUpdated && (
                    <p className="text-xs text-[var(--color-text-muted)]">
                        Updated: {new Date(lastUpdated).toLocaleDateString('en-US', {
                            month: 'short',
                            day: 'numeric',
                            hour: '2-digit',
                            minute: '2-digit',
                        })}
                    </p>
                )}
            </div>
        </aside>
    );
}
