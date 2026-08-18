import React, { useState, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Users,
  HelpCircle,
  Clock,
  Search,
  ArrowRight,
  ShieldCheck,
  CheckCircle2,
  AlertTriangle,
  Loader2,
  RefreshCw,
  Zap,
} from 'lucide-react';
import { useAuth } from '../../hooks/useAuth';
import { getAdminOverviewApi, getAdminTeamsApi } from '../../services/api';

export const AdminOverviewPage: React.FC = () => {
  const navigate = useNavigate();
  const { adminToken } = useAuth();

  const [overview, setOverview] = useState<any | null>(null);
  const [teams, setTeams] = useState<any[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const [searchTerm, setSearchTerm] = useState<string>('');
  const [statusFilter, setStatusFilter] = useState<string>('ALL');

  const fetchData = async () => {
    if (!adminToken) return;
    try {
      setError(null);
      const [ovData, teamsData] = await Promise.all([
        getAdminOverviewApi(adminToken),
        getAdminTeamsApi(adminToken),
      ]);
      setOverview(ovData);
      setTeams(teamsData);
    } catch (err: any) {
      console.error('Admin Overview Fetch Error:', err);
      setError(err?.message || 'Failed to fetch event telemetry data.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    // 5-second polling for real-time evaluator updates
    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);
  }, [adminToken]);

  const filteredTeams = useMemo(() => {
    return teams.filter((t) => {
      const matchSearch =
        t.team_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        (t.member_names &&
          t.member_names.some((m: string) =>
            m.toLowerCase().includes(searchTerm.toLowerCase())
          ));
      const matchStatus = statusFilter === 'ALL' || t.status === statusFilter;
      return matchSearch && matchStatus;
    });
  }, [teams, searchTerm, statusFilter]);

  const formatTimeAgo = (isoString?: string) => {
    if (!isoString) return 'No activity';
    const ms = Date.now() - new Date(isoString).getTime();
    const mins = Math.floor(ms / 60000);
    if (mins < 1) return 'Just now';
    if (mins === 1) return '1 min ago';
    if (mins < 60) return `${mins} mins ago`;
    const hrs = Math.floor(mins / 60);
    return `${hrs} hr(s) ago`;
  };

  const getStatusBadge = (statusStr: string) => {
    switch (statusStr) {
      case 'ACTIVE':
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-500/10 text-emerald-400 font-mono text-xs font-bold border border-emerald-500/30">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            ACTIVE
          </span>
        );
      case 'COMPLETED':
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-blue-500/10 text-blue-400 font-mono text-xs font-bold border border-blue-500/30">
            <CheckCircle2 className="w-3.5 h-3.5 text-blue-400" />
            COMPLETED
          </span>
        );
      case 'TIME_EXPIRED':
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-amber-500/10 text-amber-400 font-mono text-xs font-bold border border-amber-500/30">
            <Clock className="w-3.5 h-3.5 text-amber-400" />
            TIME EXPIRED
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-slate-800 text-slate-400 font-mono text-xs font-bold border border-slate-700">
            NOT STARTED
          </span>
        );
    }
  };

  return (
    <div className="space-y-8 select-none">
      
      {/* OVERVIEW BANNER */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl sm:text-3xl font-black tracking-tight text-white uppercase font-sans">
              EVENT EVALUATION CONTROL PANEL
            </h1>
          </div>
          <p className="text-xs sm:text-sm text-slate-400 mt-1">
            Real-time competition performance & team query evaluation.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => fetchData()}
            className="px-3.5 py-2 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-800 text-xs font-bold text-slate-200 flex items-center gap-2 transition-all"
            title="Refresh Telemetry"
          >
            <RefreshCw className="w-3.5 h-3.5 text-slate-400" />
            <span>Sync Telemetry</span>
          </button>
        </div>
      </div>

      {/* EVENT STAT CARDS (2 Columns) */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
        
        <div className="p-5 rounded-2xl bg-[#0F172A] border border-slate-800 space-y-2 shadow-lg">
          <div className="flex items-center justify-between text-slate-400 text-xs font-mono font-bold uppercase">
            <span>Registered Teams</span>
            <Users className="w-4 h-4 text-indigo-400" />
          </div>
          <div className="text-3xl font-black text-white font-mono">
            {overview?.registered_teams ?? 0}
          </div>
          <p className="text-[11px] text-slate-400 font-mono">
            Official Competition Entries
          </p>
        </div>

        <div className="p-5 rounded-2xl bg-[#0F172A] border border-slate-800 space-y-2 shadow-lg">
          <div className="flex items-center justify-between text-slate-400 text-xs font-mono font-bold uppercase">
            <span>Active Teams</span>
            <Zap className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-3xl font-black text-emerald-400 font-mono">
            {overview?.active_teams ?? 0}
          </div>
          <p className="text-[11px] text-slate-400 font-mono">
            Currently In-Arena Sessions
          </p>
        </div>

      </div>

      {/* FILTER & SEARCH CONTROL BAR */}
      <div className="p-4 rounded-2xl bg-[#0F172A] border border-slate-800 flex flex-col md:flex-row items-center justify-between gap-4 shadow-sm">
        
        {/* Search Field */}
        <div className="relative w-full md:w-80">
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search teams or members..."
            className="w-full py-2.5 pl-9 pr-4 rounded-xl bg-slate-900 border border-slate-800 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 font-mono"
          />
          <Search className="w-4 h-4 text-slate-500 absolute left-3 top-3" />
        </div>

        {/* Status Filters */}
        <div className="flex items-center gap-1.5 overflow-x-auto w-full md:w-auto pb-1 md:pb-0">
          {['ALL', 'ACTIVE', 'COMPLETED', 'TIME_EXPIRED', 'NOT_STARTED'].map((st) => (
            <button
              key={st}
              onClick={() => setStatusFilter(st)}
              className={`px-3 py-1.5 rounded-lg text-xs font-mono font-bold transition-all whitespace-nowrap ${
                statusFilter === st
                  ? 'bg-indigo-600 text-white shadow-sm'
                  : 'bg-slate-900 text-slate-400 hover:text-white hover:bg-slate-800 border border-slate-800'
              }`}
            >
              {st.replace('_', ' ')}
            </button>
          ))}
        </div>

      </div>

      {/* TEAMS EVALUATION GRID */}
      {loading ? (
        <div className="py-16 flex flex-col items-center justify-center text-slate-400 space-y-3">
          <Loader2 className="w-8 h-8 text-indigo-500 animate-spin" />
          <p className="text-xs font-mono uppercase tracking-wider">Fetching Team Telemetry...</p>
        </div>
      ) : error ? (
        <div className="p-8 rounded-2xl bg-red-950/30 border border-red-900/60 text-red-400 text-center space-y-3">
          <AlertTriangle className="w-8 h-8 text-red-500 mx-auto" />
          <p className="text-sm font-mono font-bold">{error}</p>
        </div>
      ) : filteredTeams.length === 0 ? (
        <div className="p-12 rounded-2xl bg-[#0F172A] border border-slate-800 text-center space-y-2">
          <Users className="w-8 h-8 text-slate-600 mx-auto" />
          <h3 className="text-base font-bold text-white">No teams match filter</h3>
          <p className="text-xs font-mono text-slate-400">
            Try adjusting your search query or status filter.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          {filteredTeams.map((team) => (
            <div
              key={team.team_name}
              className="p-6 rounded-2xl bg-[#0F172A] border border-slate-800 hover:border-slate-700 transition-all space-y-5 shadow-lg group flex flex-col justify-between"
            >
              <div className="space-y-4">
                
                {/* Header: Team Name & Status Badge */}
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <h3 className="text-lg font-black text-white group-hover:text-indigo-400 transition-colors uppercase">
                      {team.team_name}
                    </h3>
                    <p className="text-xs text-slate-400 font-mono mt-0.5">
                      Members: {team.member_names?.join(', ') || 'N/A'}
                    </p>
                  </div>
                  {getStatusBadge(team.status)}
                </div>

                {/* Progress / Metrics Row */}
                <div className="grid grid-cols-2 gap-3 p-3.5 rounded-xl bg-slate-900/80 border border-slate-800/80 font-mono text-xs">
                  <div>
                    <span className="text-slate-500 text-[10px] uppercase font-bold block">
                      Questions Consumed
                    </span>
                    <span className="text-white font-extrabold text-sm">
                      {team.questions_used} / {team.question_limit}
                    </span>
                  </div>

                  <div>
                    <span className="text-slate-500 text-[10px] uppercase font-bold block">
                      Last Activity
                    </span>
                    <span className="text-slate-300 font-extrabold text-xs">
                      {formatTimeAgo(team.last_activity_at)}
                    </span>
                  </div>
                </div>

              </div>

              {/* Action Button */}
              <div className="pt-2">
                <button
                  onClick={() => navigate(`/admin/teams/${encodeURIComponent(team.team_name)}`)}
                  className="w-full py-2.5 px-4 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs uppercase tracking-wider flex items-center justify-center gap-2 group-hover:translate-x-0.5 transition-all shadow-md"
                >
                  <span>Evaluate Team Prompts</span>
                  <ArrowRight className="w-4 h-4" />
                </button>
              </div>

            </div>
          ))}
        </div>
      )}

    </div>
  );
};
