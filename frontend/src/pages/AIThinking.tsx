import { useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    Brain, Shield, Clock, Hash, CheckCircle2, XCircle, ChevronDown, ChevronRight,
    Zap, ArrowRight, Cpu, Timer
} from 'lucide-react';
import type { DashboardData, RunLog, LLMCall } from '../types';

interface AIThinkingPageProps {
    data: DashboardData;
}

export function AIThinkingPage({ data }: AIThinkingPageProps) {
    const { runLogs, leaderboard } = data;
    const [selectedAgentId, setSelectedAgentId] = useState<string>('all');
    const [selectedRunId, setSelectedRunId] = useState<string>(runLogs[0]?.run_id || '');

    // Filter runs by agent
    const filteredRuns = useMemo(() => {
        if (selectedAgentId === 'all') return runLogs;
        return runLogs.filter(r => r.competitor_id === selectedAgentId);
    }, [runLogs, selectedAgentId]);

    const selectedRun = useMemo(
        () => runLogs.find(r => r.run_id === selectedRunId),
        [runLogs, selectedRunId]
    );

    const getCompetitorName = (id: string) =>
        leaderboard.find(a => a.competitor_id === id)?.name || id;

    // Global stats
    const globalStats = useMemo(() => {
        const allCalls = runLogs.flatMap(r => r.llm_calls || []);
        const totalTokens = allCalls.reduce((sum, c) => sum + (c.prompt_tokens || 0) + (c.completion_tokens || 0), 0);
        const avgLatency = allCalls.length > 0
            ? allCalls.reduce((sum, c) => sum + (c.latency_ms || 0), 0) / allCalls.length
            : 0;
        const successRate = allCalls.length > 0
            ? allCalls.filter(c => c.success).length / allCalls.length * 100
            : 0;
        return { totalCalls: allCalls.length, totalTokens, avgLatency, successRate };
    }, [runLogs]);

    if (runLogs.length === 0) {
        return (
            <div className="bg-[var(--color-bg-secondary)] rounded-xl border border-[var(--color-border-secondary)] p-12 text-center">
                <Brain className="w-16 h-16 mx-auto mb-4 text-[var(--color-text-muted)]" />
                <h2 className="text-xl font-semibold text-[var(--color-text-primary)] mb-2">
                    No Trading Sessions Yet
                </h2>
                <p className="text-[var(--color-text-secondary)]">
                    Run a trading session to see how the AI analyzes markets and makes decisions.
                </p>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            {/* Stats Row */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <StatCard icon={<Cpu className="w-5 h-5 text-blue-400" />} label="Total LLM Calls" value={globalStats.totalCalls.toString()} color="blue" />
                <StatCard icon={<Hash className="w-5 h-5 text-purple-400" />} label="Total Tokens" value={globalStats.totalTokens.toLocaleString()} color="purple" />
                <StatCard icon={<Timer className="w-5 h-5 text-amber-400" />} label="Avg Latency" value={`${(globalStats.avgLatency / 1000).toFixed(1)}s`} color="amber" />
                <StatCard icon={<CheckCircle2 className="w-5 h-5 text-emerald-400" />} label="Success Rate" value={`${globalStats.successRate.toFixed(0)}%`} color="emerald" />
            </div>

            {/* Session Selector */}
            <div className="bg-[var(--color-bg-secondary)] rounded-xl border border-[var(--color-border-secondary)] p-5">
                <div className="flex flex-col sm:flex-row sm:items-center gap-4">
                    <div className="flex-1">
                        <label className="text-xs text-[var(--color-text-muted)] mb-2 block">Filter by Agent</label>
                        <select
                            value={selectedAgentId}
                            onChange={(e) => {
                                setSelectedAgentId(e.target.value);
                                const firstRun = e.target.value === 'all' ? runLogs[0] : runLogs.find(r => r.competitor_id === e.target.value);
                                if (firstRun) setSelectedRunId(firstRun.run_id);
                            }}
                            className="w-full bg-[var(--color-bg-tertiary)] text-[var(--color-text-primary)] border border-[var(--color-border-primary)] rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-[var(--color-accent-primary)]"
                        >
                            <option value="all">All Agents</option>
                            {leaderboard.map(agent => (
                                <option key={agent.competitor_id} value={agent.competitor_id}>
                                    {agent.name}
                                </option>
                            ))}
                        </select>
                    </div>
                    <div className="flex-1 sm:flex-[2]">
                        <label className="text-xs text-[var(--color-text-muted)] mb-2 block">Select Session</label>
                        <select
                            value={selectedRunId}
                            onChange={(e) => setSelectedRunId(e.target.value)}
                            className="w-full bg-[var(--color-bg-tertiary)] text-[var(--color-text-primary)] border border-[var(--color-border-primary)] rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-[var(--color-accent-primary)]"
                        >
                            {filteredRuns.map(run => (
                                <option key={run.run_id} value={run.run_id}>
                                    {run.session_date} • {run.session_type} • {getCompetitorName(run.competitor_id)} • {run.fills.length} trades
                                </option>
                            ))}
                        </select>
                    </div>
                </div>
            </div>

            {/* Selected Run Details */}
            {selectedRun && (
                <>
                    {/* Run Header Card */}
                    <motion.div
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="bg-[var(--color-bg-secondary)] rounded-xl border border-[var(--color-border-secondary)] p-5"
                    >
                        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                            <div className="flex items-center gap-4">
                                <div className="w-12 h-12 rounded-xl bg-[var(--color-accent-primary)]/20 flex items-center justify-center">
                                    <Brain className="w-6 h-6 text-[var(--color-accent-primary)]" />
                                </div>
                                <div>
                                    <h3 className="text-lg font-semibold text-[var(--color-text-primary)]">
                                        {getCompetitorName(selectedRun.competitor_id)}
                                    </h3>
                                    <p className="text-sm text-[var(--color-text-muted)]">
                                        {selectedRun.session_date} • {selectedRun.session_type} Session
                                    </p>
                                </div>
                            </div>
                            <div className="flex gap-6">
                                <div className="text-center">
                                    <p className="text-2xl font-bold text-[var(--color-text-primary)]">{selectedRun.llm_calls.length}</p>
                                    <p className="text-xs text-[var(--color-text-muted)]">LLM Calls</p>
                                </div>
                                <div className="text-center">
                                    <p className="text-2xl font-bold text-[var(--color-text-primary)]">{selectedRun.fills.length}</p>
                                    <p className="text-xs text-[var(--color-text-muted)]">Trades</p>
                                </div>
                            </div>
                        </div>
                    </motion.div>

                    {/* LLM Reasoning Pipeline */}
                    <div className="space-y-4">
                        <h2 className="text-lg font-semibold text-[var(--color-text-primary)] flex items-center gap-2">
                            <Zap className="w-5 h-5 text-[var(--color-accent-primary)]" />
                            LLM Reasoning Pipeline
                        </h2>

                        {selectedRun.llm_calls.map((call, index) => (
                            <LLMCallCard key={index} call={call} index={index} />
                        ))}
                    </div>

                    {/* Proposal Flow */}
                    {selectedRun.strategist_proposal && selectedRun.trade_plan && (
                        <motion.div
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            className="bg-[var(--color-bg-secondary)] rounded-xl border border-[var(--color-border-secondary)] p-5"
                        >
                            <h2 className="text-lg font-semibold text-[var(--color-text-primary)] mb-5 flex items-center gap-2">
                                <Shield className="w-5 h-5 text-emerald-400" />
                                Trade Proposals & Decisions
                            </h2>
                            <ProposalFlow proposal={selectedRun.strategist_proposal} tradePlan={selectedRun.trade_plan} />
                        </motion.div>
                    )}

                    {/* Executed Trades */}
                    {selectedRun.fills.length > 0 && (
                        <motion.div
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            className="bg-[var(--color-bg-secondary)] rounded-xl border border-[var(--color-border-secondary)] p-5"
                        >
                            <h2 className="text-lg font-semibold text-[var(--color-text-primary)] mb-4">
                                Executed Trades
                            </h2>
                            <div className="overflow-x-auto">
                                <table className="w-full text-sm">
                                    <thead>
                                        <tr className="border-b border-[var(--color-border-secondary)]">
                                            <th className="text-left py-3 px-2 text-[var(--color-text-muted)] font-medium">Ticker</th>
                                            <th className="text-left py-3 px-2 text-[var(--color-text-muted)] font-medium">Side</th>
                                            <th className="text-right py-3 px-2 text-[var(--color-text-muted)] font-medium">Qty</th>
                                            <th className="text-right py-3 px-2 text-[var(--color-text-muted)] font-medium">Price</th>
                                            <th className="text-right py-3 px-2 text-[var(--color-text-muted)] font-medium">Notional</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {selectedRun.fills.map((fill, i) => (
                                            <tr key={i} className="border-b border-[var(--color-border-secondary)]/50">
                                                <td className="py-3 px-2 font-mono font-medium text-[var(--color-text-primary)]">{fill.ticker}</td>
                                                <td className="py-3 px-2">
                                                    <span className={`px-2 py-1 rounded text-xs font-medium ${fill.side === 'BUY' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-red-500/20 text-red-400'}`}>
                                                        {fill.side}
                                                    </span>
                                                </td>
                                                <td className="py-3 px-2 text-right text-[var(--color-text-primary)]">{fill.qty}</td>
                                                <td className="py-3 px-2 text-right font-mono text-[var(--color-text-primary)]">${fill.fill_price.toFixed(2)}</td>
                                                <td className="py-3 px-2 text-right font-mono text-[var(--color-text-primary)]">${fill.notional.toLocaleString()}</td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        </motion.div>
                    )}
                </>
            )}
        </div>
    );
}

function StatCard({ icon, label, value, color }: { icon: React.ReactNode; label: string; value: string; color: string }) {
    const colorClasses: Record<string, string> = {
        blue: 'bg-blue-500/20',
        purple: 'bg-purple-500/20',
        amber: 'bg-amber-500/20',
        emerald: 'bg-emerald-500/20'
    };
    return (
        <div className="bg-[var(--color-bg-secondary)] rounded-xl border border-[var(--color-border-secondary)] p-4">
            <div className="flex items-center gap-3">
                <div className={`w-10 h-10 rounded-lg ${colorClasses[color]} flex items-center justify-center`}>
                    {icon}
                </div>
                <div>
                    <p className="text-xs text-[var(--color-text-muted)]">{label}</p>
                    <p className="text-lg font-bold text-[var(--color-text-primary)]">{value}</p>
                </div>
            </div>
        </div>
    );
}

function LLMCallCard({ call, index }: { call: LLMCall; index: number }) {
    const [expanded, setExpanded] = useState<string | null>(null);

    const toggleSection = (section: string) => setExpanded(expanded === section ? null : section);

    const getCallConfig = (type: string) => {
        switch (type) {
            case 'strategist': return { icon: <Brain className="w-5 h-5" />, title: 'Strategist Agent', color: 'bg-blue-500/20 text-blue-400' };
            case 'risk_guard': return { icon: <Shield className="w-5 h-5" />, title: 'Risk Guard Agent', color: 'bg-emerald-500/20 text-emerald-400' };
            default: return { icon: <Zap className="w-5 h-5" />, title: 'JSON Repair', color: 'bg-amber-500/20 text-amber-400' };
        }
    };

    const config = getCallConfig(call.call_type);

    return (
        <div className="relative">

            <motion.div
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.05 }}
                className="bg-[var(--color-bg-secondary)] rounded-xl border border-[var(--color-border-secondary)] overflow-hidden"
            >
                {/* Header */}
                <div className="flex items-center justify-between p-4 border-b border-[var(--color-border-secondary)]">
                    <div className="flex items-center gap-3">
                        <div className={`w-10 h-10 rounded-lg ${config.color} flex items-center justify-center`}>
                            {config.icon}
                        </div>
                        <div>
                            <h3 className="font-semibold text-[var(--color-text-primary)]">{config.title}</h3>
                            <p className="text-xs text-[var(--color-text-muted)]">Latency: {call.latency_ms}ms</p>
                        </div>
                    </div>
                    <div className="flex items-center gap-3 text-sm">
                        <span className="text-[var(--color-text-muted)] hidden sm:inline"><Clock className="w-4 h-4 inline mr-1" />{call.latency_ms}ms</span>
                        <span className="text-[var(--color-text-muted)] hidden sm:inline"><Hash className="w-4 h-4 inline mr-1" />{(call.prompt_tokens || 0) + (call.completion_tokens || 0)}</span>
                        {call.success ? <CheckCircle2 className="w-5 h-5 text-emerald-400" /> : <XCircle className="w-5 h-5 text-red-400" />}
                    </div>
                </div>

                {/* Expandable Sections */}
                <div className="divide-y divide-[var(--color-border-secondary)]">
                    {call.system_prompt && (
                        <ExpandSection title="System Prompt" icon={<Cpu className="w-4 h-4" />} expanded={expanded === 'system'} onClick={() => toggleSection('system')}>
                            <pre className="bg-[var(--color-bg-tertiary)] rounded-lg p-4 text-xs text-[var(--color-text-secondary)] whitespace-pre-wrap overflow-x-auto max-h-48 overflow-y-auto">{call.system_prompt}</pre>
                        </ExpandSection>
                    )}
                    {call.prompt && (
                        <ExpandSection title="Market Briefing" icon={<Brain className="w-4 h-4" />} expanded={expanded === 'prompt'} onClick={() => toggleSection('prompt')}>
                            <pre className="bg-[var(--color-bg-tertiary)] rounded-lg p-4 text-xs text-[var(--color-text-secondary)] whitespace-pre-wrap overflow-x-auto max-h-48 overflow-y-auto">{call.prompt}</pre>
                        </ExpandSection>
                    )}
                    {call.raw_response && (
                        <ExpandSection title="LLM Response" icon={<ArrowRight className="w-4 h-4" />} expanded={expanded === 'output'} onClick={() => toggleSection('output')}>
                            <pre className="bg-[var(--color-bg-tertiary)] rounded-lg p-4 text-xs text-[var(--color-text-secondary)] overflow-x-auto max-h-48 overflow-y-auto">{formatJSON(call.raw_response)}</pre>
                        </ExpandSection>
                    )}
                </div>

                {call.error && (
                    <div className="p-4 bg-red-500/10 border-t border-red-500/20">
                        <p className="text-sm text-red-400">Error: {call.error}</p>
                    </div>
                )}
            </motion.div>
        </div>
    );
}

function ExpandSection({ title, icon, expanded, onClick, children }: { title: string; icon: React.ReactNode; expanded: boolean; onClick: () => void; children: React.ReactNode }) {
    return (
        <div>
            <button onClick={onClick} className="w-full flex items-center justify-between p-4 hover:bg-[var(--color-bg-tertiary)] transition-colors">
                <span className="flex items-center gap-2 text-sm font-medium text-[var(--color-text-secondary)]">{icon}{title}</span>
                {expanded ? <ChevronDown className="w-4 h-4 text-[var(--color-text-muted)]" /> : <ChevronRight className="w-4 h-4 text-[var(--color-text-muted)]" />}
            </button>
            <AnimatePresence>
                {expanded && (
                    <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }} exit={{ height: 0, opacity: 0 }} className="overflow-hidden">
                        <div className="p-4 pt-0">{children}</div>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
}

function ProposalFlow({ proposal, tradePlan }: { proposal: NonNullable<RunLog['strategist_proposal']>; tradePlan: NonNullable<RunLog['trade_plan']> }) {
    const approvedTickers = new Set(tradePlan.orders.map(o => o.ticker));

    return (
        <div className="space-y-4">
            {proposal.market_summary && (
                <div className="p-4 bg-[var(--color-bg-tertiary)] rounded-lg">
                    <p className="text-xs text-[var(--color-text-muted)] mb-1">Market Summary</p>
                    <p className="text-sm text-[var(--color-text-primary)]">{proposal.market_summary}</p>
                </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {proposal.proposals.map((prop, idx) => {
                    const isApproved = approvedTickers.has(prop.ticker);
                    const order = tradePlan.orders.find(o => o.ticker === prop.ticker);

                    return (
                        <div
                            key={idx}
                            className={`p-4 rounded-lg border ${isApproved ? 'border-emerald-500/30 bg-emerald-500/5' : prop.action === 'HOLD' ? 'border-[var(--color-border-secondary)] bg-[var(--color-bg-tertiary)]' : 'border-red-500/30 bg-red-500/5'}`}
                        >
                            <div className="flex items-center justify-between mb-2">
                                <div className="flex items-center gap-2">
                                    <span className="font-mono font-bold text-[var(--color-text-primary)]">{prop.ticker}</span>
                                    <span className={`px-2 py-0.5 rounded text-xs font-medium ${prop.action === 'BUY' ? 'bg-emerald-500/20 text-emerald-400' : prop.action === 'SELL' ? 'bg-red-500/20 text-red-400' : 'bg-gray-500/20 text-gray-400'}`}>
                                        {prop.action}
                                    </span>
                                </div>
                                <span className={`text-sm font-bold ${prop.confidence >= 0.7 ? 'text-emerald-400' : prop.confidence >= 0.5 ? 'text-amber-400' : 'text-red-400'}`}>
                                    {(prop.confidence * 100).toFixed(0)}%
                                </span>
                            </div>
                            <p className="text-xs text-[var(--color-text-secondary)] mb-3">{prop.rationale}</p>
                            <div className="flex items-center gap-2 pt-2 border-t border-[var(--color-border-secondary)]">
                                <ArrowRight className="w-4 h-4 text-[var(--color-text-muted)]" />
                                {isApproved && order ? (
                                    <span className="text-xs text-emerald-400 font-medium">✓ Approved → {order.side} {order.qty} shares</span>
                                ) : prop.action === 'HOLD' ? (
                                    <span className="text-xs text-[var(--color-text-muted)]">Hold (no action)</span>
                                ) : (
                                    <span className="text-xs text-red-400">✗ Vetoed by Risk Guard</span>
                                )}
                            </div>
                        </div>
                    );
                })}
            </div>

            {tradePlan.risk_assessment && (
                <div className="p-4 bg-amber-500/10 border border-amber-500/20 rounded-lg">
                    <p className="text-xs font-medium text-amber-400 mb-1">Risk Assessment</p>
                    <p className="text-sm text-[var(--color-text-secondary)]">{tradePlan.risk_assessment}</p>
                </div>
            )}
        </div>
    );
}

function formatJSON(str: string): string {
    try { return JSON.stringify(JSON.parse(str), null, 2); }
    catch { return str; }
}
