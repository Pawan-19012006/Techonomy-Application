import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  ArrowLeft,
  Users,
  Clock,
  HelpCircle,
  FileText,
  ChevronDown,
  ChevronUp,
  Loader2,
  AlertCircle,
  ExternalLink,
  CheckCircle2,
  BookOpen,
} from 'lucide-react';
import { useAuth } from '../../hooks/useAuth';
import { getAdminTeamDetailApi } from '../../services/api';

export const AdminTeamDetailPage: React.FC = () => {
  const { teamName } = useParams<{ teamName: string }>();
  const navigate = useNavigate();
  const { adminToken } = useAuth();

  const [teamDetail, setTeamDetail] = useState<any | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const [expandedQueries, setExpandedQueries] = useState<{ [key: number]: boolean }>({});

  const cleanTeamName = teamName ? decodeURIComponent(teamName) : '';

  const fetchDetail = async () => {
    if (!adminToken || !cleanTeamName) return;
    try {
      setError(null);
      const data = await getAdminTeamDetailApi(adminToken, cleanTeamName);
      setTeamDetail(data);
      // Auto-expand all queries by default for fast evaluation
      if (data?.prompts) {
        const initialMap: { [key: number]: boolean } = {};
        data.prompts.forEach((p: any) => {
          initialMap[p.id] = true;
        });
        setExpandedQueries(initialMap);
      }
    } catch (err: any) {
      console.error('Admin Team Detail Error:', err);
      setError(err?.message || `Unable to load evaluation details for team '${cleanTeamName}'.`);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDetail();
    // 5s polling to catch live incoming team queries during evaluation
    const interval = setInterval(fetchDetail, 5000);
    return () => clearInterval(interval);
  }, [adminToken, cleanTeamName]);

  const toggleExpand = (id: number) => {
    setExpandedQueries((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  const handleCitationClick = (docName: string, pageNum?: number) => {
    const pageParam = pageNum ? `?page=${pageNum}` : '';
    navigate(`/admin/documents/${encodeURIComponent(docName)}${pageParam}`);
  };

  return (
    <div className="space-y-8 select-none">
      
      {/* NAVIGATION & TEAM HEADER */}
      <div className="space-y-4">
        
        <button
          onClick={() => navigate('/admin')}
          className="px-3 py-1.5 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-800 text-xs font-mono font-bold text-slate-300 flex items-center gap-2 transition-all"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to All Teams</span>
        </button>

        {loading && !teamDetail ? (
          <div className="py-12 flex flex-col items-center justify-center text-slate-400 space-y-3">
            <Loader2 className="w-8 h-8 text-indigo-500 animate-spin" />
            <p className="text-xs font-mono uppercase tracking-wider">Loading Team Evaluation Payload...</p>
          </div>
        ) : error ? (
          <div className="p-6 rounded-2xl bg-red-950/30 border border-red-900/60 text-red-400 font-mono text-xs text-center space-y-2">
            <AlertCircle className="w-6 h-6 text-red-500 mx-auto" />
            <p>{error}</p>
          </div>
        ) : teamDetail ? (
          <div className="p-6 sm:p-8 rounded-2xl bg-[#0F172A] border border-slate-800 space-y-6 shadow-xl">
            
            {/* Header Title & Status */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-slate-800">
              <div>
                <h1 className="text-3xl font-black text-white uppercase tracking-tight font-sans">
                  {teamDetail.team_name}
                </h1>
                <p className="text-xs text-slate-400 font-mono mt-1 flex items-center gap-2">
                  <Users className="w-4 h-4 text-indigo-400" />
                  <span>Members: {teamDetail.member_names?.join(', ') || 'N/A'}</span>
                </p>
              </div>

              <div className="flex items-center gap-3">
                <span className="px-3.5 py-1.5 rounded-full bg-indigo-500/10 text-indigo-400 font-mono text-xs font-bold border border-indigo-500/30 uppercase">
                  Status: {teamDetail.status}
                </span>
              </div>
            </div>

            {/* Quick Metrics Bar */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 font-mono text-xs">
              <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800">
                <span className="text-slate-400 text-[10px] uppercase font-bold block">
                  Questions Consumed
                </span>
                <span className="text-white font-extrabold text-base mt-1 block">
                  {teamDetail.questions_used} / {teamDetail.question_limit}
                </span>
              </div>

              <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800">
                <span className="text-slate-400 text-[10px] uppercase font-bold block">
                  Remaining Tokens
                </span>
                <span className="text-emerald-400 font-extrabold text-base mt-1 block">
                  {teamDetail.questions_remaining} Tokens
                </span>
              </div>

              <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800">
                <span className="text-slate-400 text-[10px] uppercase font-bold block">
                  Session Started
                </span>
                <span className="text-slate-300 font-bold text-xs mt-1 block truncate">
                  {teamDetail.started_at
                    ? new Date(teamDetail.started_at).toLocaleTimeString()
                    : 'N/A'}
                </span>
              </div>
            </div>

          </div>
        ) : null}

      </div>

      {/* PROMPT EXECUTION HISTORY */}
      {teamDetail && (
        <div className="space-y-6">
          
          <div className="flex items-center justify-between pb-2 border-b border-slate-800">
            <h2 className="text-xl font-extrabold text-white uppercase tracking-tight">
              PROMPT EXECUTION HISTORY ({teamDetail.prompts?.length || 0})
            </h2>
            <span className="text-xs font-mono text-slate-400">
              Chronological Evaluator Trail
            </span>
          </div>

          {teamDetail.prompts?.length === 0 ? (
            <div className="p-12 rounded-2xl bg-[#0F172A] border border-slate-800 text-center space-y-2">
              <HelpCircle className="w-8 h-8 text-slate-600 mx-auto" />
              <h3 className="text-base font-bold text-white">No Prompts Submitted Yet</h3>
              <p className="text-xs font-mono text-slate-400">
                This team has not executed any RAG queries during their session.
              </p>
            </div>
          ) : (
            <div className="space-y-5">
              {teamDetail.prompts.map((log: any, idx: number) => {
                const queryNumber = teamDetail.prompts.length - idx;
                const isExpanded = expandedQueries[log.id] !== false;

                return (
                  <div
                    key={log.id}
                    className="rounded-2xl bg-[#0F172A] border border-slate-800 overflow-hidden shadow-lg transition-all"
                  >
                    
                    {/* Entry Header */}
                    <button
                      onClick={() => toggleExpand(log.id)}
                      className="w-full p-4 sm:p-5 flex items-center justify-between gap-4 bg-slate-900/60 hover:bg-slate-900 border-b border-slate-800/80 transition-colors text-left"
                    >
                      <div className="flex items-center gap-3 min-w-0">
                        <span className="px-2.5 py-1 rounded bg-indigo-600 text-white font-mono text-xs font-bold shrink-0">
                          QUERY #{queryNumber.toString().padStart(2, '0')}
                        </span>
                        <h3 className="text-sm font-bold text-white truncate max-w-xl">
                          "{log.prompt}"
                        </h3>
                      </div>

                      <div className="flex items-center gap-4 shrink-0">
                        <span className="text-[11px] font-mono text-slate-400 hidden sm:inline">
                          {log.created_at ? new Date(log.created_at).toLocaleTimeString() : ''}
                        </span>
                        {isExpanded ? (
                          <ChevronUp className="w-4 h-4 text-slate-400" />
                        ) : (
                          <ChevronDown className="w-4 h-4 text-slate-400" />
                        )}
                      </div>
                    </button>

                    {/* Entry Details */}
                    {isExpanded && (
                      <div className="p-5 sm:p-6 space-y-6">
                        
                        {/* Question */}
                        <div className="space-y-1.5">
                          <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-slate-400">
                            QUESTION SUBMITTED
                          </span>
                          <div className="p-3.5 rounded-xl bg-slate-900 border border-slate-800 text-sm font-medium text-slate-100 font-sans">
                            {log.prompt}
                          </div>
                        </div>

                        {/* RAG Answer */}
                        <div className="space-y-1.5">
                          <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-indigo-400">
                            KAIROS GENERATED RESPONSE
                          </span>
                          <div className="p-4 rounded-xl bg-slate-900/90 border border-indigo-900/40 text-sm text-slate-200 leading-relaxed font-sans whitespace-pre-wrap">
                            {log.response}
                          </div>
                        </div>

                        {/* RAG Citation Sources */}
                        {log.sources && log.sources.length > 0 ? (
                          <div className="space-y-2 pt-2 border-t border-slate-800/80">
                            <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-amber-400 flex items-center gap-1.5">
                              <BookOpen className="w-3.5 h-3.5" />
                              RETRIEVED DOCUMENT SOURCES ({log.sources.length})
                            </span>

                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                              {log.sources.map((src: any, sIdx: number) => (
                                <button
                                  key={sIdx}
                                  onClick={() => handleCitationClick(src.document, src.page)}
                                  className="flex items-center justify-between gap-3 p-3 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-800 hover:border-indigo-500/50 text-left transition-all group cursor-pointer"
                                >
                                  <div className="flex items-center gap-2.5 min-w-0">
                                    <div className="p-1.5 rounded-lg bg-indigo-950 text-indigo-400 border border-indigo-900">
                                      <FileText className="w-3.5 h-3.5" />
                                    </div>
                                    <div className="truncate">
                                      <p className="text-xs font-bold text-white group-hover:text-indigo-400 truncate">
                                        {src.document}
                                      </p>
                                      <p className="text-[10px] font-mono text-slate-400">
                                        {src.page != null ? `Page ${src.page}` : 'Indexed Source'}
                                      </p>
                                    </div>
                                  </div>

                                  <ExternalLink className="w-3.5 h-3.5 text-slate-500 group-hover:text-white shrink-0" />
                                </button>
                              ))}
                            </div>
                          </div>
                        ) : (
                          <div className="pt-2 border-t border-slate-800/80">
                            <span className="text-[11px] font-mono text-slate-500 italic">
                              No source references recorded for this query.
                            </span>
                          </div>
                        )}

                      </div>
                    )}

                  </div>
                );
              })}
            </div>
          )}

        </div>
      )}

    </div>
  );
};
