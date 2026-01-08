import { useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    Brain,
    Shield,
    Clock,
    Hash,
    CheckCircle2,
    XCircle,
    ChevronDown,
    ChevronRight,
    Zap,
    ArrowRight
} from 'lucide-react';
import type { DashboardData, RunLog, LLMCall } from '../types';

interface AIThinkingPageProps {
    data: DashboardData;
}

export function AIThinkingPage({ data }: AIThinkingPageProps) {
    const { runLogs, leaderboard } = data;
    const [selectedRunId, setSelectedRunId] = useState<string>(runLogs[0]?.run_id || '');

    const selectedRun = useMemo(
        () => runLogs.find(r => r.run_id === selectedRunId),
        [runLogs, selectedRunId]
    );

    // Get competitor name
    const getCompetitorName = (id: string) =>
        leaderboard.find(a => a.competitor_id === id)?.name || id;

    return (
        <div className="space-y-8">
            {/* Page Header */}
            <motion.div
                initial={{ opacity: 0, y: -20 }}
                animate={{ opacity: 1, y: 0 }}
            >
                <h1 className="text-3xl font-bold gradient-text mb-2">AI Thinking Process</h1>
                <p className="text-[var(--color-text-secondary)]">
                    Explore how the AI analyzes markets and makes trading decisions
                </p>
            </motion.div>

            {/* Empty State */}
            {runLogs.length === 0 ? (
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="glass-card p-12 text-center"
                >
                    <Brain className="w-16 h-16 mx-auto mb-4 text-[var(--color-text-muted)]" />
                    <h2 className="text-xl font-semibold text-[var(--color-text-primary)] mb-2">
                        No Trading Sessions Yet
                    </h2>
                    <p className="text-[var(--color-text-secondary)]">
                        Run a trading session to see how the AI analyzes markets and makes decisions.
                    </p>
                </motion.div>
            ) : (
                <>
                    {/* Run Selector */}
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="glass-card p-6"
                    >
                        <label className="block text-sm font-medium text-[var(--color-text-secondary)] mb-2">
                            Select Trading Session
                        </label>
                        <select
                            value={selectedRunId}
                            onChange={(e) => setSelectedRunId(e.target.value)}
                            className="w-full md:w-96 bg-[var(--color-bg-tertiary)] text-[var(--color-text-primary)] border border-[var(--color-border-primary)] rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-[var(--color-accent-primary)]"
                        >
                            {runLogs.map(run => (
                                <option key={run.run_id} value={run.run_id}>
                                    {run.session_date} {run.session_type} — {getCompetitorName(run.competitor_id)}
                                </option>
                            ))}
                        </select>
                    </motion.div>

                    {selectedRun && (
                        <>
                            {/* Run Overview */}
                            <motion.div
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: 0.1 }}
                                className="grid grid-cols-2 md:grid-cols-4 gap-4"
                            >
                                <MetricCard label="Date" value={selectedRun.session_date} />
                                <MetricCard label="Session" value={selectedRun.session_type} />
                                <MetricCard label="Agent" value={getCompetitorName(selectedRun.competitor_id)} />
                                <MetricCard label="Trades Executed" value={selectedRun.fills.length.toString()} />
                            </motion.div>

                            {/* LLM Calls Timeline */}
                            <motion.div
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: 0.2 }}
                                className="space-y-6"
                            >
                                <h2 className="text-xl font-semibold text-[var(--color-text-primary)]">
                                    LLM Reasoning Pipeline
                                </h2>

                                {selectedRun.llm_calls.map((call, index) => (
                                    <LLMCallCard
                                        key={index}
                                        call={call}
                                        index={index}
                                        isLast={index === selectedRun.llm_calls.length - 1}
                                    />
                                ))}
                            </motion.div>

                            {/* Proposal → Decision Flow */}
                            {selectedRun.strategist_proposal && selectedRun.trade_plan && (
                                <motion.div
                                    initial={{ opacity: 0, y: 20 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    transition={{ delay: 0.3 }}
                                    className="glass-card p-6"
                                >
                                    <h2 className="text-xl font-semibold text-[var(--color-text-primary)] mb-6">
                                        Proposal → Decision Flow
                                    </h2>
                                    <ProposalFlow
                                        proposal={selectedRun.strategist_proposal}
                                        tradePlan={selectedRun.trade_plan}
                                    />
                                </motion.div>
                            )}

                            {/* Executed Trades */}
                            {selectedRun.fills.length > 0 && (
                                <motion.div
                                    initial={{ opacity: 0, y: 20 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    transition={{ delay: 0.4 }}
                                    className="glass-card p-6"
                                >
                                    <h2 className="text-xl font-semibold text-[var(--color-text-primary)] mb-4">
                                        Executed Trades
                                    </h2>
                                    <table className="data-table">
                                        <thead>
                                            <tr>
                                                <th>Ticker</th>
                                                <th>Side</th>
                                                <th>Quantity</th>
                                                <th>Fill Price</th>
                                                <th>Notional</th>
                                                <th>Fees</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {selectedRun.fills.map((fill, index) => (
                                                <tr key={index}>
                                                    <td className="font-mono font-medium">{fill.ticker}</td>
                                                    <td>
                                                        <span className={`badge ${fill.side === 'BUY' ? 'badge-success' : 'badge-danger'}`}>
                                                            {fill.side}
                                                        </span>
                                                    </td>
                                                    <td>{fill.qty}</td>
                                                    <td className="font-mono">${fill.fill_price.toFixed(2)}</td>
                                                    <td className="font-mono">${fill.notional.toLocaleString()}</td>
                                                    <td className="font-mono text-[var(--color-text-muted)]">${fill.fees.toFixed(2)}</td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </motion.div>
                            )}
                        </>
                    )}
                </>
            )}
        </div>
    );
}

// Metric Card Component
function MetricCard({ label, value }: { label: string; value: string }) {
    return (
        <div className="glass-card p-4">
            <p className="text-xs text-[var(--color-text-muted)] mb-1">{label}</p>
            <p className="text-lg font-semibold text-[var(--color-text-primary)]">{value}</p>
        </div>
    );
}

// LLM Call Card Component
function LLMCallCard({ call, index, isLast }: { call: LLMCall; index: number; isLast: boolean }) {
    const [expandedSections, setExpandedSections] = useState<Record<string, boolean>>({});

    const toggleSection = (section: string) => {
        setExpandedSections(prev => ({ ...prev, [section]: !prev[section] }));
    };

    const getCallIcon = (type: string) => {
        switch (type) {
            case 'strategist':
                return <Brain className="w-5 h-5" />;
            case 'risk_guard':
                return <Shield className="w-5 h-5" />;
            default:
                return <Zap className="w-5 h-5" />;
        }
    };

    const getCallTitle = (type: string) => {
        switch (type) {
            case 'strategist':
                return 'Strategist Agent';
            case 'risk_guard':
                return 'Risk Guard Agent';
            case 'repair':
                return 'JSON Repair';
            default:
                return type;
        }
    };

    return (
        <div className="relative">
            {/* Connection Line */}
            {!isLast && (
                <div className="absolute left-6 top-20 bottom-0 w-0.5 bg-gradient-to-b from-[var(--color-accent-primary)] to-transparent" />
            )}

            <motion.div
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.15 }}
                className="glass-card overflow-hidden"
            >
                {/* Header */}
                <div className="flex items-center justify-between p-4 border-b border-[var(--color-border-primary)] bg-[var(--color-bg-tertiary)]">
                    <div className="flex items-center gap-3">
                        <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${call.call_type === 'strategist'
                            ? 'bg-blue-500/20 text-blue-400'
                            : call.call_type === 'risk_guard'
                                ? 'bg-green-500/20 text-green-400'
                                : 'bg-yellow-500/20 text-yellow-400'
                            }`}>
                            {getCallIcon(call.call_type)}
                        </div>
                        <div>
                            <h3 className="font-semibold text-[var(--color-text-primary)]">
                                {getCallTitle(call.call_type)}
                            </h3>
                            <p className="text-xs text-[var(--color-text-muted)]">
                                {call.provider}/{call.model}
                            </p>
                        </div>
                    </div>

                    <div className="flex items-center gap-4">
                        {/* Metrics */}
                        <div className="hidden sm:flex items-center gap-4 text-sm">
                            <div className="flex items-center gap-1.5 text-[var(--color-text-secondary)]">
                                <Clock className="w-4 h-4" />
                                <span>{call.latency_ms}ms</span>
                            </div>
                            <div className="flex items-center gap-1.5 text-[var(--color-text-secondary)]">
                                <Hash className="w-4 h-4" />
                                <span>{call.prompt_tokens + call.completion_tokens} tokens</span>
                            </div>
                        </div>

                        {/* Status */}
                        {call.success ? (
                            <CheckCircle2 className="w-5 h-5 text-[var(--color-accent-success)]" />
                        ) : (
                            <XCircle className="w-5 h-5 text-[var(--color-accent-danger)]" />
                        )}
                    </div>
                </div>

                {/* Expandable Sections */}
                <div className="divide-y divide-[var(--color-border-secondary)]">
                    {/* System Prompt */}
                    {call.system_prompt && (
                        <ExpandableSection
                            title="System Prompt"
                            isExpanded={expandedSections['system']}
                            onToggle={() => toggleSection('system')}
                            icon="⚙️"
                        >
                            <pre className="code-block text-xs whitespace-pre-wrap overflow-x-auto">
                                {call.system_prompt}
                            </pre>
                        </ExpandableSection>
                    )}

                    {/* User Prompt */}
                    {call.prompt && (
                        <ExpandableSection
                            title="User Prompt (Market Briefing)"
                            isExpanded={expandedSections['prompt']}
                            onToggle={() => toggleSection('prompt')}
                            icon="📝"
                        >
                            <pre className="code-block text-xs whitespace-pre-wrap overflow-x-auto max-h-96 overflow-y-auto">
                                {call.prompt}
                            </pre>
                        </ExpandableSection>
                    )}

                    {/* Raw Output */}
                    {call.raw_response && (
                        <ExpandableSection
                            title="Raw Output (JSON)"
                            isExpanded={expandedSections['output']}
                            onToggle={() => toggleSection('output')}
                            icon="📤"
                        >
                            <pre className="code-block text-xs overflow-x-auto">
                                <code>{formatJSON(call.raw_response)}</code>
                            </pre>
                        </ExpandableSection>
                    )}
                </div>

                {/* Error */}
                {call.error && (
                    <div className="p-4 bg-red-500/10 border-t border-red-500/20">
                        <p className="text-sm text-[var(--color-accent-danger)]">
                            Error: {call.error}
                        </p>
                    </div>
                )}
            </motion.div>
        </div>
    );
}

// Expandable Section Component
function ExpandableSection({
    title,
    isExpanded,
    onToggle,
    icon,
    children,
}: {
    title: string;
    isExpanded: boolean;
    onToggle: () => void;
    icon: string;
    children: React.ReactNode;
}) {
    return (
        <div>
            <button
                onClick={onToggle}
                className="w-full flex items-center justify-between p-4 hover:bg-[var(--color-bg-tertiary)] transition-colors"
            >
                <div className="flex items-center gap-2">
                    <span>{icon}</span>
                    <span className="text-sm font-medium text-[var(--color-text-secondary)]">{title}</span>
                </div>
                {isExpanded ? (
                    <ChevronDown className="w-4 h-4 text-[var(--color-text-muted)]" />
                ) : (
                    <ChevronRight className="w-4 h-4 text-[var(--color-text-muted)]" />
                )}
            </button>
            <AnimatePresence>
                {isExpanded && (
                    <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        transition={{ duration: 0.2 }}
                        className="overflow-hidden"
                    >
                        <div className="p-4 pt-0">{children}</div>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
}

// Proposal Flow Visualization
function ProposalFlow({
    proposal,
    tradePlan
}: {
    proposal: NonNullable<RunLog['strategist_proposal']>;
    tradePlan: NonNullable<RunLog['trade_plan']>;
}) {
    const approvedTickers = new Set(tradePlan.orders.map(o => o.ticker));

    return (
        <div className="space-y-4">
            {/* Market Summary */}
            {proposal.market_summary && (
                <div className="p-4 bg-[var(--color-bg-tertiary)] rounded-lg mb-6">
                    <p className="text-sm text-[var(--color-text-secondary)] mb-1">Market Summary</p>
                    <p className="text-[var(--color-text-primary)]">{proposal.market_summary}</p>
                </div>
            )}

            {/* Proposals Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {proposal.proposals.map((prop, index) => {
                    const isApproved = approvedTickers.has(prop.ticker);
                    const order = tradePlan.orders.find(o => o.ticker === prop.ticker);

                    return (
                        <motion.div
                            key={prop.ticker}
                            initial={{ opacity: 0, scale: 0.95 }}
                            animate={{ opacity: 1, scale: 1 }}
                            transition={{ delay: index * 0.1 }}
                            className={`p-4 rounded-lg border ${isApproved
                                ? 'border-[var(--color-accent-success)]/30 bg-[var(--color-accent-success)]/5'
                                : prop.action === 'HOLD'
                                    ? 'border-[var(--color-border-primary)] bg-[var(--color-bg-secondary)]'
                                    : 'border-[var(--color-accent-danger)]/30 bg-[var(--color-accent-danger)]/5'
                                }`}
                        >
                            <div className="flex items-start justify-between mb-3">
                                <div className="flex items-center gap-2">
                                    <span className="font-mono font-bold text-lg text-[var(--color-text-primary)]">
                                        {prop.ticker}
                                    </span>
                                    <span className={`badge ${prop.action === 'BUY' ? 'badge-success' :
                                        prop.action === 'SELL' ? 'badge-danger' :
                                            'badge-warning'
                                        }`}>
                                        {prop.action}
                                    </span>
                                </div>
                                <div className="text-right">
                                    <p className="text-xs text-[var(--color-text-muted)]">Confidence</p>
                                    <p className={`font-bold ${prop.confidence >= 0.7 ? 'value-positive' :
                                        prop.confidence >= 0.5 ? 'text-[var(--color-accent-warning)]' :
                                            'value-negative'
                                        }`}>
                                        {(prop.confidence * 100).toFixed(0)}%
                                    </p>
                                </div>
                            </div>

                            <p className="text-sm text-[var(--color-text-secondary)] mb-3">
                                {prop.rationale}
                            </p>

                            {/* Decision Arrow */}
                            <div className="flex items-center gap-2 pt-3 border-t border-[var(--color-border-secondary)]">
                                <ArrowRight className="w-4 h-4 text-[var(--color-text-muted)]" />
                                {isApproved && order ? (
                                    <span className="text-sm text-[var(--color-accent-success)] font-medium">
                                        ✓ APPROVED → {order.side} {order.qty} shares
                                    </span>
                                ) : prop.action === 'HOLD' ? (
                                    <span className="text-sm text-[var(--color-text-muted)]">
                                        No action (HOLD)
                                    </span>
                                ) : (
                                    <span className="text-sm text-[var(--color-accent-danger)]">
                                        ✗ VETOED
                                    </span>
                                )}
                            </div>
                        </motion.div>
                    );
                })}
            </div>

            {/* Risk Assessment */}
            {tradePlan.risk_assessment && (
                <div className="mt-6 p-4 bg-yellow-500/10 border border-yellow-500/20 rounded-lg">
                    <p className="text-sm font-medium text-yellow-400 mb-1">Risk Assessment</p>
                    <p className="text-sm text-[var(--color-text-secondary)]">{tradePlan.risk_assessment}</p>
                </div>
            )}
        </div>
    );
}

// Helper function to format JSON with syntax highlighting classes
function formatJSON(jsonString: string): string {
    try {
        const parsed = JSON.parse(jsonString);
        return JSON.stringify(parsed, null, 2);
    } catch {
        return jsonString;
    }
}
