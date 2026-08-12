import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Sparkles, Users, UserCheck, AlertCircle, ArrowRight } from 'lucide-react';
import { joinTeam } from '../services/api';
import { useAuth } from '../hooks/useAuth';
import { toast } from 'sonner';

const teamEntrySchema = z.object({
  team_name: z.string().min(1, 'Team Name is required').max(100, 'Team Name is too long'),
  member_names_str: z.string().min(1, 'At least one Member Name is required'),
});

type TeamEntryFormValues = z.infer<typeof teamEntrySchema>;

export const LoginPage: React.FC = () => {
  const navigate = useNavigate();
  const { loginTeam } = useAuth();
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<TeamEntryFormValues>({
    resolver: zodResolver(teamEntrySchema),
    defaultValues: {
      team_name: 'TEAM-01',
      member_names_str: 'Pawan, Rahul, Kabilan',
    },
  });

  const onSubmit = async (values: TeamEntryFormValues) => {
    try {
      setErrorMessage(null);
      
      const member_names = values.member_names_str
        .split(',')
        .map((name) => name.trim())
        .filter((name) => name.length > 0);

      if (member_names.length === 0) {
        setErrorMessage('Please enter at least one member name.');
        return;
      }

      const teamData = await joinTeam(values.team_name.trim(), member_names);
      
      // Store team information and update auth state
      loginTeam(teamData);
      
      toast.success(`Welcome Team ${teamData.team_name}! Entering Arena.`);
      navigate('/dashboard');
    } catch (err: any) {
      console.error('Team Entry failed:', err);
      const userFacingMsg = err?.userMessage || err?.response?.data?.detail || 'Unable to connect to the Techonomy server. Please try again.';
      setErrorMessage(userFacingMsg);
      toast.error(userFacingMsg);
    }
  };

  return (
    <div className="min-h-screen bg-[#111827] flex items-center justify-center p-4 sm:p-6 lg:p-8">
      <div className="w-full max-w-md space-y-6">
        {/* Brand Header */}
        <div className="text-center space-y-2">
          <div className="w-14 h-14 rounded-2xl bg-indigo-600 text-white flex items-center justify-center mx-auto shadow-lg shadow-indigo-600/30">
            <Sparkles className="w-8 h-8" />
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-white">
            TECHONOMY
          </h1>
          <p className="text-xs font-medium uppercase tracking-widest text-slate-400">
            Enterprise Knowledge Intelligence Platform
          </p>
        </div>

        {/* Card */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 sm:p-8 shadow-2xl space-y-6">
          <div className="border-b border-slate-800 pb-4">
            <h2 className="text-lg font-bold text-white">Enter Team Arena</h2>
            <p className="text-xs text-slate-400 mt-1">
              Enter your Team Name and Member Names to start the challenge
            </p>
          </div>

          {errorMessage && (
            <div className="p-3.5 rounded-xl bg-red-950/40 border border-red-800/60 text-red-300 text-xs flex items-center gap-2.5">
              <AlertCircle className="w-4 h-4 shrink-0 text-red-400" />
              <span>{errorMessage}</span>
            </div>
          )}

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            {/* Team Name */}
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-slate-300">
                Team Name
              </label>
              <div className="relative">
                <input
                  type="text"
                  {...register('team_name')}
                  className="w-full bg-slate-950 border border-slate-800 focus:border-indigo-500 text-white rounded-xl py-2.5 px-3.5 pl-10 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/20"
                  placeholder="e.g. TEAM-01"
                />
                <Users className="w-4 h-4 text-slate-500 absolute left-3.5 top-3" />
              </div>
              {errors.team_name && (
                <p className="text-[11px] text-red-400">{errors.team_name.message}</p>
              )}
            </div>

            {/* Member Names */}
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-slate-300">
                Member Names (Comma separated)
              </label>
              <div className="relative">
                <input
                  type="text"
                  {...register('member_names_str')}
                  className="w-full bg-slate-950 border border-slate-800 focus:border-indigo-500 text-white rounded-xl py-2.5 px-3.5 pl-10 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/20"
                  placeholder="e.g. Pawan, Rahul, Kabilan"
                />
                <UserCheck className="w-4 h-4 text-slate-500 absolute left-3.5 top-3" />
              </div>
              {errors.member_names_str && (
                <p className="text-[11px] text-red-400">{errors.member_names_str.message}</p>
              )}
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full bg-indigo-600 hover:bg-indigo-500 text-white font-semibold py-3 px-4 rounded-xl text-sm transition-colors flex items-center justify-center gap-2 shadow-lg shadow-indigo-600/30 disabled:opacity-50 mt-2"
            >
              {isSubmitting ? 'Entering Arena...' : 'Enter Arena'}
              <ArrowRight className="w-4 h-4" />
            </button>
          </form>

          <div className="pt-4 border-t border-slate-800/80 text-center text-xs text-slate-500 space-y-1">
            <p>Example: <code className="text-indigo-400">TEAM-01</code></p>
          </div>
        </div>
      </div>
    </div>
  );
};
