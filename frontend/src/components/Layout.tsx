import type { ReactNode } from 'react';
import { Sidebar } from './Sidebar';

interface LayoutProps {
    children: ReactNode;
    lastUpdated?: string;
}

export function Layout({ children, lastUpdated }: LayoutProps) {
    return (
        <div className="min-h-screen bg-[var(--color-bg-primary)]">
            <Sidebar lastUpdated={lastUpdated} />
            <main className="ml-64 min-h-screen">
                <div className="p-8">
                    {children}
                </div>
            </main>
        </div>
    );
}
