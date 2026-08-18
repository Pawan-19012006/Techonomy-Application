import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, Trash2, ArrowRight, AlertCircle, Sparkles, ShieldCheck, Users } from 'lucide-react';
import { joinTeam, adminLoginApi } from '../services/api';
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

          if (dist < 130) {
            ctx.strokeStyle = `rgba(255, 255, 255, ${0.12 * (1 - dist / 130)})`;
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
  const { loginTeam, loginAdmin } = useAuth();

  const [loginRole, setLoginRole] = useState<'PARTICIPANT' | 'ADMIN'>('PARTICIPANT');

  // Participant Form State
  const [teamName, setTeamName] = useState('');
  const [members, setMembers] = useState<MemberRow[]>([
    { id: '1', name: '', roll: '' },
  ]);

  // Admin Form State
  const [adminUsername, setAdminUsername] = useState('');
  const [adminPassword, setAdminPassword] = useState('');

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
    setFieldErrors((prev) => {
      const copy = { ...prev };
      delete copy[`${id}_${field}`];
      return copy;
    });
  };

  const validateParticipantForm = (): boolean => {
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

  const handleParticipantSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);

    if (!validateParticipantForm()) {
      return;
    }

    try {
      setIsSubmitting(true);
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

  const handleAdminSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);

    if (!adminUsername.trim() || !adminPassword.trim()) {
      setErrorMessage('Username and password are required.');
      return;
    }

    try {
      setIsSubmitting(true);
      const res = await adminLoginApi(adminUsername.trim(), adminPassword.trim());
      loginAdmin(res.access_token);
      toast.success('Admin authentication successful! Opening Control Panel.');
      navigate('/admin');
    } catch (err: any) {
      console.error('Admin login error:', err);
      setErrorMessage('Invalid admin credentials.');
      toast.error('Invalid admin credentials.');
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
            {loginRole === 'ADMIN' ? 'ADMIN ACCESS CONTROL' : 'TEAM ENTRY'}
          </p>
        </div>

        {/* Bottom Footer Label */}
        <div className="relative z-10 text-[11px] font-mono text-slate-500 tracking-wider">
          SYSTEM_ID // KAIROS_V2.0
        </div>

      </div>

      {/* RIGHT SIDE (~50% Viewport) — Login Form */}
      <div className="lg:w-1/2 w-full flex-1 bg-[#F8FAFC] dark:bg-[#0F172A] flex flex-col justify-center p-6 sm:p-12 lg:p-16 transition-colors overflow-y-auto">
        <div className="max-w-xl w-full mx-auto space-y-8">
          
          {/* ROLE SELECTOR TAB TOGGLE */}
          <div className="flex items-center p-1 rounded-2xl bg-slate-200/80 dark:bg-slate-900 border border-slate-300/80 dark:border-slate-800">
            <button
              type="button"
              onClick={() => {
                setLoginRole('PARTICIPANT');
                setErrorMessage(null);
              }}
              className={`flex-1 py-2.5 px-4 rounded-xl text-xs font-bold uppercase tracking-wider flex items-center justify-center gap-2 transition-all ${
                loginRole === 'PARTICIPANT'
                  ? 'bg-white dark:bg-slate-800 text-slate-950 dark:text-white shadow-sm'
                  : 'text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
              }`}
            >
              <Users className="w-4 h-4" />
              <span>Participant</span>
            </button>

            <button
              type="button"
              onClick={() => {
                setLoginRole('ADMIN');
                setErrorMessage(null);
              }}
              className={`flex-1 py-2.5 px-4 rounded-xl text-xs font-bold uppercase tracking-wider flex items-center justify-center gap-2 transition-all ${
                loginRole === 'ADMIN'
                  ? 'bg-indigo-600 text-white shadow-md'
                  : 'text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
              }`}
            >
              <ShieldCheck className="w-4 h-4" />
              <span>Admin Access</span>
            </button>
          </div>

          {/* Header Title */}
          <div className="space-y-1">
            <h2 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-slate-950 dark:text-white uppercase">
              {loginRole === 'ADMIN' ? 'ADMINISTRATOR ACCESS' : 'TEAM ENTRY'}
            </h2>
            <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400">
              {loginRole === 'ADMIN'
                ? 'Authorized event organizers only. Enter admin credentials.'
                : 'Enter your team details to proceed into the event workspace.'}
            </p>
          </div>

          {errorMessage && (
            <div className="p-3.5 rounded-xl bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-900/60 text-red-700 dark:text-red-300 text-xs flex items-center gap-2.5">
              <AlertCircle className="w-4 h-4 shrink-0 text-red-500" />
              <span>{errorMessage}</span>
            </div>
          )}

          {/* PARTICIPANT LOGIN FORM */}
          {loginRole === 'PARTICIPANT' ? (
            <form onSubmit={handleParticipantSubmit} className="space-y-6">
              
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
                  placeholder="Enter team name"
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

                <div className="space-y-3">
                  {members.map((m, index) => (
                    <div
                      key={m.id}
                      className="p-3.5 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 space-y-2 transition-all shadow-xs"
                    >
                      <div className="flex items-center justify-between">
                        <span className="text-[11px] font-mono font-bold text-slate-400 uppercase">
                          MEMBER {index + 1}
                        </span>
                        {members.length > 1 && (
                          <button
                            type="button"
                            onClick={() => handleRemoveMember(m.id)}
                            className="p-1 text-slate-400 hover:text-red-500 transition-colors"
                            title="Remove Member"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        )}
                      </div>

                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                        <div>
                          <input
                            type="text"
                            value={m.name}
                            onChange={(e) => handleMemberChange(m.id, 'name', e.target.value)}
                            placeholder="Student Full Name"
                            className={`kairos-input w-full text-xs py-2 px-3 ${
                              fieldErrors[`${m.id}_name`]
                                ? 'border-red-500 focus:border-red-500'
                                : ''
                            }`}
                          />
                        </div>

                        <div>
                          <input
                            type="text"
                            value={m.roll}
                            onChange={(e) => handleMemberChange(m.id, 'roll', e.target.value)}
                            placeholder="Roll Number"
                            className={`kairos-input w-full text-xs py-2 px-3 ${
                              fieldErrors[`${m.id}_roll`]
                                ? 'border-red-500 focus:border-red-500'
                                : ''
                            }`}
                          />
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* SUBMIT BUTTON */}
              <button
                type="submit"
                disabled={isSubmitting}
                className="kairos-btn-primary w-full py-4 text-base font-bold uppercase tracking-wider flex items-center justify-center gap-2 group shadow-md"
              >
                <span>{isSubmitting ? 'JOINING ARENA...' : 'ENTER KAIROS ARENA'}</span>
                <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
              </button>

            </form>
          ) : (
            /* ADMIN LOGIN FORM */
            <form onSubmit={handleAdminSubmit} className="space-y-6">
              
              <div className="space-y-2">
                <label className="text-xs font-extrabold tracking-wider text-slate-900 dark:text-slate-200 uppercase block">
                  ADMIN USERNAME
                </label>
                <input
                  type="text"
                  value={adminUsername}
                  onChange={(e) => setAdminUsername(e.target.value)}
                  placeholder="Username"
                  className="kairos-input w-full py-3.5 px-4 text-base font-semibold"
                />
              </div>

              <div className="space-y-2">
                <label className="text-xs font-extrabold tracking-wider text-slate-900 dark:text-slate-200 uppercase block">
                  ADMIN PASSWORD
                </label>
                <input
                  type="password"
                  value={adminPassword}
                  onChange={(e) => setAdminPassword(e.target.value)}
                  placeholder="Password"
                  className="kairos-input w-full py-3.5 px-4 text-base font-semibold"
                />
              </div>

              <button
                type="submit"
                disabled={isSubmitting}
                className="kairos-btn-primary w-full py-4 text-base font-bold uppercase tracking-wider flex items-center justify-center gap-2 group shadow-md bg-indigo-600 hover:bg-indigo-500"
              >
                <span>{isSubmitting ? 'VERIFYING...' : 'ENTER ADMIN CONTROL PANEL'}</span>
                <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
              </button>

            </form>
          )}

        </div>
      </div>

    </div>
  );
};
