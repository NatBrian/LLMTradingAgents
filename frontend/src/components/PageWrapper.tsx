import { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Menu, X, LineChart } from 'lucide-react';

interface PageWrapperProps {
    children: React.ReactNode;
    title?: string;
    subtitle?: string;
}

const NAV_ITEMS = [
    { path: '/', label: 'Dashboard' },
    { path: '/trades', label: 'Trades' },
    { path: '/thinking', label: 'AI Thinking' },
    { path: '/market', label: 'Markets' },
    { path: '/portfolio', label: 'Portfolio' },
    { path: '/architecture', label: 'About' },
];

export function PageWrapper({ children, title, subtitle }: PageWrapperProps) {
    const location = useLocation();
    const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

    return (
        <div className="min-h-screen bg-[var(--color-bg-primary)]">
            {/* Header with Navigation - Matches Dashboard style */}
            <header className="border-b border-[var(--color-border-secondary)] bg-[var(--color-bg-primary)]/80 backdrop-blur-sm sticky top-0 z-50">
                <div className="max-w-[1600px] mx-auto px-4 sm:px-6 py-4">
                    <div className="flex items-center justify-between">
                        {/* Logo */}
                        <Link to="/" className="flex items-center gap-3">
                            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-[var(--color-accent-primary)] to-[var(--color-accent-secondary)] flex items-center justify-center">
                                <LineChart className="w-5 h-5 text-white" />
                            </div>
                            <div>
                                <h1 className="text-lg font-bold text-[var(--color-text-primary)]">Trading Arena</h1>
                                <p className="text-xs text-[var(--color-text-muted)]">LLM Trading Competition</p>
                            </div>
                        </Link>

                        {/* Desktop Navigation */}
                        <nav className="hidden md:flex items-center gap-1">
                            {NAV_ITEMS.map(item => (
                                <Link
                                    key={item.path}
                                    to={item.path}
                                    className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${location.pathname === item.path
                                        ? 'bg-[var(--color-accent-primary)] text-white'
                                        : 'text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)] hover:bg-[var(--color-bg-tertiary)]'
                                        }`}
                                >
                                    {item.label}
                                </Link>
                            ))}
                        </nav>

                        {/* Mobile Menu Button */}
                        <button
                            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                            className="md:hidden p-2 rounded-lg text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)] hover:bg-[var(--color-bg-tertiary)]"
                        >
                            {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
                        </button>
                    </div>

                    {/* Mobile Navigation */}
                    {mobileMenuOpen && (
                        <nav className="md:hidden mt-4 pb-2 border-t border-[var(--color-border-secondary)] pt-4">
                            <div className="flex flex-col gap-1">
                                {NAV_ITEMS.map(item => (
                                    <Link
                                        key={item.path}
                                        to={item.path}
                                        onClick={() => setMobileMenuOpen(false)}
                                        className={`px-4 py-3 rounded-lg text-sm font-medium transition-colors ${location.pathname === item.path
                                            ? 'bg-[var(--color-accent-primary)] text-white'
                                            : 'text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)] hover:bg-[var(--color-bg-tertiary)]'
                                            }`}
                                    >
                                        {item.label}
                                    </Link>
                                ))}
                            </div>
                        </nav>
                    )}
                </div>
            </header>

            {/* Page Content */}
            <main className="max-w-[1600px] mx-auto px-4 sm:px-6 py-6">
                {(title || subtitle) && (
                    <div className="mb-6">
                        {title && (
                            <h1 className="text-2xl lg:text-3xl font-bold text-[var(--color-text-primary)]">
                                {title}
                            </h1>
                        )}
                        {subtitle && (
                            <p className="text-[var(--color-text-muted)] text-sm mt-1">
                                {subtitle}
                            </p>
                        )}
                    </div>
                )}
                {children}
            </main>
        </div>
    );
}
