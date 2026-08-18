import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, Trash2, ArrowRight, AlertCircle, Sparkles } from 'lucide-react';
import { joinTeam } from '../services/api';
import { useAuth } from '../hooks/useAuth';
import { toast } from 'sonner';

interface MemberRow {
  id: string;
  name: string;
  roll: string;
}

// Subtle, performant canvas network animation for the left visual area
const NetworkBackground: React.FC = () => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animationFrameId: number;
    let width = (canvas.width = canvas.parentElement?.clientWidth || 600);
    let height = (canvas.height = canvas.parentElement?.clientHeight || 800);

    const handleResize = () => {
      if (!canvas || !canvas.parentElement) return;
      width = canvas.width = canvas.parentElement.clientWidth;
      height = canvas.height = canvas.parentElement.clientHeight;
    };

    window.addEventListener('resize', handleResize);

    // Generate random nodes
    const nodeCount = 28;
    const nodes = Array.from({ length: nodeCount }, () => ({
      x: Math.random() * width,
      y: Math.random() * height,
      vx: (Math.random() - 0.5) * 0.3,
      vy: (Math.random() - 0.5) * 0.3,
      radius: Math.random() * 2 + 1,
    }));

    const render = () => {
      ctx.clearRect(0, 0, width, height);

      // Draw subtle grid lines
      ctx.strokeStyle = 'rgba(255, 255, 255, 0.025)';
      ctx.lineWidth = 1;
      const gridSize = 60;
      for (let x = 0; x < width; x += gridSize) {
        ctx.beginPath();
        ctx.moveTo(x, 0);
        ctx.lineTo(x, height);
        ctx.stroke();
      }
      for (let y = 0; y < height; y += gridSize) {
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(width, y);
        ctx.stroke();
      }

      // Update and draw nodes
      nodes.forEach((node, i) => {
        node.x += node.vx;
        node.y += node.vy;

        if (node.x < 0 || node.x > width) node.vx *= -1;
        if (node.y < 0 || node.y > height) node.vy *= -1;

        ctx.fillStyle = 'rgba(255, 255, 255, 0.35)';
        ctx.beginPath();
        ctx.arc(node.x, node.y, node.radius, 0, Math.PI * 2);
        ctx.fill();

        // Connect nearby nodes
        for (let j = i + 1; j < nodes.length; j++) {
          const other = nodes[j];
          const dx = other.x - node.x;
          const dy = other.y - node.y;
          const dist = Math.sqrt(dx * dx + dy * dy);

          if (dist < 140) {
            ctx.strokeStyle = `rgba(255, 255, 255, ${0.08 * (1 - dist / 140)})`;
            ctx.lineWidth = 0.8;
            ctx.beginPath();
            ctx.moveTo(node.x, node.y);
            ctx.lineTo(other.x, other.y);
            ctx.stroke();
          }
        }
      });

      animationFrameId = requestAnimationFrame(render);
    };

    render();

    return () => {
      window.removeEventListener('resize', handleResize);
      cancelAnimationFrame(animationFrameId);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      className="absolute inset-0 w-full h-full pointer-events-none opacity-80"
    />
  );
};

export const LoginPage: React.FC = () => {
  const navigate = useNavigate();
  const { loginTeam } = useAuth();

  const [teamName, setTeamName] = useState('');
  const [members, setMembers] = useState<MemberRow[]>([
    { id: '1', name: '', roll: '' },
  ]);

  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<{ [key: string]: string }>({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  const MAX_MEMBERS = 4;

  const handleAddMember = () => {
    if (members.length >= MAX_MEMBERS) return;
    const newMember: MemberRow = {
      id: Date.now().toString(),
      name: '',
      roll: '',
    };
    setMembers((prev) => [...prev, newMember]);
  };

  const handleRemoveMember = (id: string) => {
    if (members.length <= 1) return;
    setMembers((prev) => prev.filter((m) => m.id !== id));
  };

  const handleMemberChange = (id: string, field: 'name' | 'roll', value: string) => {
    setMembers((prev) =>
      prev.map((m) => (m.id === id ? { ...m, [field]: value } : m))
    );
    // Clear validation error when user types
    setFieldErrors((prev) => {
      const copy = { ...prev };
      delete copy[`${id}_${field}`];
      return copy;
    });
  };

  const validateForm = (): boolean => {
    const errors: { [key: string]: string } = {};

    if (!teamName.trim()) {
      errors.teamName = 'Team name is required';
    }

    members.forEach((m, index) => {
      if (!m.name.trim()) {
        errors[`${m.id}_name`] = `Member ${index + 1} name required`;
      }
      if (!m.roll.trim()) {
        errors[`${m.id}_roll`] = `Roll number required`;
      }
    });

    setFieldErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);

    if (!validateForm()) {
      return;
    }

    try {
      setIsSubmitting(true);

      // Format member string: "Student Name (Roll No)"
      const formattedMemberNames = members.map(
        (m) => `${m.name.trim()}${m.roll.trim() ? ` (${m.roll.trim()})` : ''}`
      );

      const teamData = await joinTeam(teamName.trim(), formattedMemberNames);

      loginTeam(teamData);
      toast.success(`Welcome ${teamData.team_name}! Entering Kairos.`);
      navigate('/dashboard');
    } catch (err: any) {
      console.error('Login error:', err);
      const userMsg =
        err?.userMessage ||
        err?.response?.data?.detail ||
        'Unable to connect to Kairos backend server.';
      setErrorMessage(userMsg);
      toast.error(userMsg);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen w-full bg-[#090D16] flex flex-col lg:flex-row overflow-hidden select-none">
      
      {/* LEFT SIDE (~50% Viewport) — KAIROS Visual Identity */}
      <div className="relative lg:w-1/2 w-full min-h-[320px] lg:min-h-screen bg-gradient-to-br from-[#0B0F19] via-[#090D16] to-[#04060A] flex flex-col justify-between p-8 sm:p-12 lg:p-16 border-b lg:border-b-0 lg:border-r border-slate-800/80 overflow-hidden">
        
        {/* Animated Canvas */}
        <NetworkBackground />

        {/* Ambient Glow Orbs */}
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-indigo-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-slate-500/5 rounded-full blur-3xl pointer-events-none" />

        {/* Top Header Mark */}
        <div className="relative z-10 flex items-center gap-2">
          <div className="w-8 h-8 rounded-xl bg-white text-slate-950 flex items-center justify-center font-bold shadow-md">
            <Sparkles className="w-4 h-4 fill-current" />
          </div>
          <span className="text-xs font-mono font-semibold tracking-widest uppercase text-slate-400">
            KAIROS ARENA
          </span>
        </div>

        {/* Center Dominant Brand Wordmark */}
        <div className="relative z-10 my-auto py-12 space-y-4">
          <h1 className="text-6xl sm:text-7xl lg:text-8xl font-extrabold tracking-tighter text-white uppercase leading-none drop-shadow-sm font-sans">
            KAIROS
          </h1>
          <p className="text-xs sm:text-sm font-bold tracking-[0.35em] uppercase text-slate-400 pl-1">
            TEAM ENTRY
          </p>
        </div>

        {/* Bottom Footer Label */}
        <div className="relative z-10 text-[11px] font-mono text-slate-500 tracking-wider">
          SYSTEM_ID // KAIROS_V2.0
        </div>

      </div>

      {/* RIGHT SIDE (~50% Viewport) — Team Entry Form */}
      <div className="lg:w-1/2 w-full flex-1 bg-[#F8FAFC] dark:bg-[#0F172A] flex flex-col justify-center p-6 sm:p-12 lg:p-16 transition-colors overflow-y-auto">
        <div className="max-w-xl w-full mx-auto space-y-8">
          
          {/* Header */}
          <div className="space-y-1">
            <h2 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-slate-950 dark:text-white uppercase">
              TEAM ENTRY
            </h2>
            <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400">
              Enter your team details to proceed into the event workspace.
            </p>
          </div>

          {errorMessage && (
            <div className="p-3.5 rounded-xl bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-900/60 text-red-700 dark:text-red-300 text-xs flex items-center gap-2.5">
              <AlertCircle className="w-4 h-4 shrink-0 text-red-500" />
              <span>{errorMessage}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-6">
            
            {/* TEAM NAME FIELD */}
            <div className="space-y-2">
              <label className="text-xs font-extrabold tracking-wider text-slate-900 dark:text-slate-200 uppercase block">
                TEAM NAME
              </label>
              <input
                type="text"
                value={teamName}
                onChange={(e) => {
                  setTeamName(e.target.value);
                  setFieldErrors((prev) => {
                    const c = { ...prev };
                    delete c.teamName;
                    return c;
                  });
                }}
                placeholder="[ Enter team name ]"
                className={`kairos-input w-full py-3.5 px-4 text-base font-semibold ${
                  fieldErrors.teamName
                    ? 'border-red-500 focus:border-red-500 focus:ring-red-500/20'
                    : ''
                }`}
              />
              {fieldErrors.teamName && (
                <p className="text-xs text-red-500 font-medium pl-1">
                  {fieldErrors.teamName}
                </p>
              )}
            </div>

            {/* TEAM MEMBERS SECTION */}
            <div className="space-y-3 pt-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-extrabold tracking-wider text-slate-900 dark:text-slate-200 uppercase">
                  TEAM MEMBERS ({members.length}/{MAX_MEMBERS})
                </span>

                {members.length < MAX_MEMBERS && (
                  <button
                    type="button"
                    onClick={handleAddMember}
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-900 dark:bg-white text-white dark:text-slate-950 text-xs font-bold hover:opacity-90 transition-all shadow-sm active:scale-95"
                  >
                    <Plus className="w-3.5 h-3.5" />
                    <span>Add Member</span>
                  </button>
                )}
              </div>

              {/* Members Rows */}
              <div className="space-y-3">
                {members.map((member, idx) => (
                  <div
                    key={member.id}
                    className="p-3.5 rounded-xl bg-white dark:bg-[#141C2E] border border-slate-200/90 dark:border-slate-800 shadow-sm space-y-2 transition-all duration-200"
                  >
                    <div className="flex items-center justify-between text-[11px] font-bold text-slate-400 uppercase tracking-wider">
                      <span>MEMBER {idx + 1}</span>
                      {members.length > 1 && (
                        <button
                          type="button"
                          onClick={() => handleRemoveMember(member.id)}
                          className="text-slate-400 hover:text-red-500 transition-colors p-1"
                          title="Remove Member"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      )}
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-12 gap-3">
                      {/* Student Name */}
                      <div className="sm:col-span-7 space-y-1">
                        <input
                          type="text"
                          value={member.name}
                          onChange={(e) =>
                            handleMemberChange(member.id, 'name', e.target.value)
                          }
                          placeholder="Student Name"
                          className={`kairos-input w-full py-2.5 px-3 text-sm ${
                            fieldErrors[`${member.id}_name`]
                              ? 'border-red-500'
                              : ''
                          }`}
                        />
                        {fieldErrors[`${member.id}_name`] && (
                          <p className="text-[10px] text-red-500 font-medium">
                            {fieldErrors[`${member.id}_name`]}
                          </p>
                        )}
                      </div>

                      {/* Roll Number */}
                      <div className="sm:col-span-5 space-y-1">
                        <input
                          type="text"
                          value={member.roll}
                          onChange={(e) =>
                            handleMemberChange(member.id, 'roll', e.target.value)
                          }
                          placeholder="Roll Number"
                          className={`kairos-input w-full py-2.5 px-3 text-sm ${
                            fieldErrors[`${member.id}_roll`]
                              ? 'border-red-500'
                              : ''
                          }`}
                        />
                        {fieldErrors[`${member.id}_roll`] && (
                          <p className="text-[10px] text-red-500 font-medium">
                            {fieldErrors[`${member.id}_roll`]}
                          </p>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* ENTER KAIROS CTA BUTTON */}
            <div className="pt-4">
              <button
                type="submit"
                disabled={isSubmitting}
                className="w-full py-4 px-6 rounded-xl font-extrabold text-sm sm:text-base tracking-wider uppercase bg-slate-950 text-white dark:bg-white dark:text-slate-950 hover:bg-slate-800 dark:hover:bg-slate-100 transition-all duration-150 shadow-md flex items-center justify-center gap-3 active:scale-[0.99] disabled:opacity-40 disabled:cursor-not-allowed group"
              >
                {isSubmitting ? (
                  <span>ENTERING KAIROS...</span>
                ) : (
                  <>
                    <span>ENTER KAIROS</span>
                    <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
                  </>
                )}
              </button>
            </div>

          </form>
        </div>
      </div>

    </div>
  );
};
