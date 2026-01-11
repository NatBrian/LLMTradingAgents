import { motion } from 'framer-motion';
import {
    Database,
    Brain,
    Shield,
    Wallet,
    BarChart3,
    FileText,
    ArrowRight,
    Zap,
    Cloud,
    Clock
} from 'lucide-react';

export function ArchitecturePage() {
    return (
        <div className="space-y-8">
            {/* Overview */}
            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="glass-card p-8"
            >
                <h2 className="text-xl font-semibold text-[var(--color-text-primary)] mb-6">
                    3-Agent Trading System
                </h2>

                {/* Visual Flow */}
                <div className="flex flex-col lg:flex-row items-stretch gap-4 mb-8">
                    {/* Market Data */}
                    <FlowCard
                        icon={<BarChart3 className="w-6 h-6" />}
                        title="Market Data"
                        subtitle="6 Data Sources"
                        color="blue"
                        items={[
                            'Price history (yfinance)',
                            'Technical indicators',
                            'Fundamentals (SEC)',
                            'Earnings calendar',
                            'Insider transactions',
                            'News sentiment',
                        ]}
                    />

                    <FlowArrow />

                    {/* Strategist */}
                    <FlowCard
                        icon={<Brain className="w-6 h-6" />}
                        title="Strategist Agent"
                        subtitle="LLM Call #1"
                        color="indigo"
                        items={[
                            'Analyzes all market data',
                            'Identifies trading signals',
                            'Proposes BUY/SELL/HOLD',
                            'Sets confidence levels',
                        ]}
                    />

                    <FlowArrow />

                    {/* Risk Guard */}
                    <FlowCard
                        icon={<Shield className="w-6 h-6" />}
                        title="Risk Guard Agent"
                        subtitle="LLM Call #2"
                        color="green"
                        items={[
                            'Validates proposals',
                            'Checks portfolio limits',
                            'Sizes positions',
                            'Approves or vetoes',
                        ]}
                    />

                    <FlowArrow />

                    {/* Broker */}
                    <FlowCard
                        icon={<Wallet className="w-6 h-6" />}
                        title="SimBroker"
                        subtitle="Execution"
                        color="yellow"
                        items={[
                            'Executes orders',
                            'Applies slippage/fees',
                            'Tracks positions',
                            'Computes P&L',
                        ]}
                    />
                </div>
            </motion.div>

            {/* Data Sources */}
            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.1 }}
                className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
            >
                <DataSourceCard
                    icon={<BarChart3 className="w-5 h-5" />}
                    title="Price Data"
                    source="Exchange via yfinance"
                    description="OHLCV data, 52-week range, volume patterns"
                />
                <DataSourceCard
                    icon={<Zap className="w-5 h-5" />}
                    title="Technical Indicators"
                    source="Computed (standard formulas)"
                    description="RSI, MACD, Moving Averages (20/50/200)"
                />
                <DataSourceCard
                    icon={<FileText className="w-5 h-5" />}
                    title="Fundamentals"
                    source="SEC Filings via yfinance"
                    description="P/E ratio, EPS, margins, debt/equity"
                />
                <DataSourceCard
                    icon={<Clock className="w-5 h-5" />}
                    title="Earnings Calendar"
                    source="Company IR"
                    description="Next earnings date, days until event"
                />
                <DataSourceCard
                    icon={<Database className="w-5 h-5" />}
                    title="Insider Transactions"
                    source="SEC Form 4"
                    description="Recent buys/sells by executives"
                />
                <DataSourceCard
                    icon={<Cloud className="w-5 h-5" />}
                    title="News Sentiment"
                    source="Alpha Vantage (optional)"
                    description="Articles with NLP sentiment scores"
                />
            </motion.div>

            {/* Technical Details */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                {/* LLM Providers */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.2 }}
                    className="glass-card p-6"
                >
                    <h3 className="text-lg font-semibold text-[var(--color-text-primary)] mb-4">
                        LLM Providers
                    </h3>
                    <div className="space-y-4">
                        <ProviderCard
                            name="Google Gemini"
                            models={['gemini-2.5-flash', 'gemini-2.5-pro']}
                            color="blue"
                        />
                        <ProviderCard
                            name="OpenRouter"
                            models={['mistral-7b-instruct', 'mimo-v2-flash']}
                            color="purple"
                        />
                    </div>
                </motion.div>

                {/* Simulation */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.3 }}
                    className="glass-card p-6"
                >
                    <h3 className="text-lg font-semibold text-[var(--color-text-primary)] mb-4">
                        Simulation Parameters
                    </h3>
                    <div className="space-y-3">
                        <ParamRow label="Initial Cash" value="$100,000" />
                        <ParamRow label="Slippage" value="10 basis points" />
                        <ParamRow label="Transaction Fees" value="10 basis points" />
                        <ParamRow label="Max Position Size" value="25% of portfolio" />
                        <ParamRow label="Max Orders/Session" value="3" />
                        <ParamRow label="Trading Sessions" value="Market Open & Close" />
                    </div>
                </motion.div>
            </div>

            {/* Deployment */}
            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.4 }}
                className="glass-card p-6"
            >
                <h3 className="text-lg font-semibold text-[var(--color-text-primary)] mb-4">
                    Deployment Architecture
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <DeploymentCard
                        title="GitHub Actions"
                        role="Runner"
                        description="Executes trading sessions at market open/close (2x daily)"
                    />
                    <DeploymentCard
                        title="SQLite (Git)"
                        role="Database"
                        description="arena.db stored in repo, committed after each session"
                    />
                    <DeploymentCard
                        title="Vercel"
                        role="Dashboard"
                        description="React frontend auto-deploys on repo changes"
                    />
                </div>
            </motion.div>
        </div>
    );
}

// Flow Card Component
function FlowCard({
    icon,
    title,
    subtitle,
    color,
    items,
}: {
    icon: React.ReactNode;
    title: string;
    subtitle: string;
    color: 'blue' | 'indigo' | 'green' | 'yellow';
    items: string[];
}) {
    const colorClasses = {
        blue: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
        indigo: 'bg-indigo-500/20 text-indigo-400 border-indigo-500/30',
        green: 'bg-green-500/20 text-green-400 border-green-500/30',
        yellow: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
    };

    return (
        <div className={`flex-1 rounded-xl border p-5 ${colorClasses[color]}`}>
            <div className="flex items-center gap-3 mb-4">
                <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${colorClasses[color]}`}>
                    {icon}
                </div>
                <div>
                    <h4 className="font-semibold text-[var(--color-text-primary)]">{title}</h4>
                    <p className="text-xs text-[var(--color-text-muted)]">{subtitle}</p>
                </div>
            </div>
            <ul className="space-y-1">
                {items.map((item, i) => (
                    <li key={i} className="text-sm text-[var(--color-text-secondary)] flex items-center gap-2">
                        <span className="w-1 h-1 rounded-full bg-current opacity-50" />
                        {item}
                    </li>
                ))}
            </ul>
        </div>
    );
}

// Flow Arrow
function FlowArrow() {
    return (
        <div className="hidden lg:flex items-center justify-center w-8">
            <ArrowRight className="w-5 h-5 text-[var(--color-text-muted)]" />
        </div>
    );
}

// Data Source Card
function DataSourceCard({
    icon,
    title,
    source,
    description,
}: {
    icon: React.ReactNode;
    title: string;
    source: string;
    description: string;
}) {
    return (
        <div className="glass-card p-5">
            <div className="flex items-center gap-3 mb-3">
                <div className="w-9 h-9 rounded-lg bg-[var(--color-bg-tertiary)] flex items-center justify-center text-[var(--color-accent-primary)]">
                    {icon}
                </div>
                <div>
                    <h4 className="font-medium text-[var(--color-text-primary)]">{title}</h4>
                    <p className="text-xs text-[var(--color-accent-secondary)]">{source}</p>
                </div>
            </div>
            <p className="text-sm text-[var(--color-text-secondary)]">{description}</p>
        </div>
    );
}

// Provider Card
function ProviderCard({
    name,
    models,
    color,
}: {
    name: string;
    models: string[];
    color: 'blue' | 'purple';
}) {
    const badgeClass = color === 'blue'
        ? 'bg-blue-500/15 text-blue-400'
        : 'bg-purple-500/15 text-purple-400';

    return (
        <div className="flex items-center justify-between p-3 bg-[var(--color-bg-tertiary)] rounded-lg">
            <span className={`badge ${badgeClass}`}>{name}</span>
            <div className="flex gap-2">
                {models.map(model => (
                    <span key={model} className="text-xs text-[var(--color-text-muted)] font-mono">
                        {model}
                    </span>
                ))}
            </div>
        </div>
    );
}

// Param Row
function ParamRow({ label, value }: { label: string; value: string }) {
    return (
        <div className="flex items-center justify-between py-2 border-b border-[var(--color-border-secondary)] last:border-0">
            <span className="text-sm text-[var(--color-text-secondary)]">{label}</span>
            <span className="text-sm font-medium text-[var(--color-text-primary)]">{value}</span>
        </div>
    );
}

// Deployment Card
function DeploymentCard({
    title,
    role,
    description,
}: {
    title: string;
    role: string;
    description: string;
}) {
    return (
        <div className="p-5 bg-[var(--color-bg-tertiary)] rounded-xl">
            <div className="flex items-center gap-2 mb-2">
                <span className="font-semibold text-[var(--color-text-primary)]">{title}</span>
                <span className="badge badge-primary text-xs">{role}</span>
            </div>
            <p className="text-sm text-[var(--color-text-secondary)]">{description}</p>
        </div>
    );
}
