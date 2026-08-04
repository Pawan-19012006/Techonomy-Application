import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Sparkles, Lock, Mail, AlertCircle, ArrowRight } from 'lucide-react';
import { loginApi } from '../api/auth';
import { useAuth } from '../hooks/useAuth';
import { toast } from 'sonner';

const loginSchema = z.object({
  email: z.string().email('Please enter a valid Team email address'),
  password: z.string().min(1, 'Password is required'),
  rememberMe: z.boolean(),
});

type LoginFormValues = z.infer<typeof loginSchema>;

export const LoginPage: React.FC = () => {
  const navigate = useNavigate();
  const { login } = useAuth();
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      email: 'devs@acme.com',
      password: 'SecretPassword123!',
      rememberMe: true,
    },
  });

  const onSubmit = async (values: LoginFormValues) => {
    try {
      setErrorMessage(null);
      const data = await loginApi(values.email, values.password);
      await login(data.access_token, values.rememberMe);
      toast.success('Authentication successful! Welcome to Techonomy.');
      navigate('/dashboard');
    } catch (err: any) {
      console.error('Login failed:', err);
      const detail = err?.response?.data?.detail || 'Invalid Team ID/Email or Password';
      setErrorMessage(detail);
      toast.error(detail);
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
            <h2 className="text-lg font-bold text-white">Sign In to Team Workspace</h2>
            <p className="text-xs text-slate-400 mt-1">
              Enter your Team ID credentials to access challenge data
            </p>
          </div>

          {errorMessage && (
            <div className="p-3.5 rounded-xl bg-red-950/40 border border-red-800/60 text-red-300 text-xs flex items-center gap-2.5">
              <AlertCircle className="w-4 h-4 shrink-0 text-red-400" />
              <span>{errorMessage}</span>
            </div>
          )}

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            {/* Email / Team ID */}
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-slate-300">
                Team Email / ID
              </label>
              <div className="relative">
                <input
                  type="email"
                  {...register('email')}
                  className="w-full bg-slate-950 border border-slate-800 focus:border-indigo-500 text-white rounded-xl py-2.5 px-3.5 pl-10 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/20"
                  placeholder="devs@acme.com"
                />
                <Mail className="w-4 h-4 text-slate-500 absolute left-3.5 top-3" />
              </div>
              {errors.email && (
                <p className="text-[11px] text-red-400">{errors.email.message}</p>
              )}
            </div>

            {/* Password */}
            <div className="space-y-1.5">
              <div className="flex items-center justify-between">
                <label className="text-xs font-semibold text-slate-300">
                  Password
                </label>
              </div>
              <div className="relative">
                <input
                  type="password"
                  {...register('password')}
                  className="w-full bg-slate-950 border border-slate-800 focus:border-indigo-500 text-white rounded-xl py-2.5 px-3.5 pl-10 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/20"
                  placeholder="••••••••••••"
                />
                <Lock className="w-4 h-4 text-slate-500 absolute left-3.5 top-3" />
              </div>
              {errors.password && (
                <p className="text-[11px] text-red-400">{errors.password.message}</p>
              )}
            </div>

            {/* Remember Me */}
            <div className="flex items-center justify-between pt-1">
              <label className="flex items-center gap-2 cursor-pointer text-xs text-slate-400">
                <input
                  type="checkbox"
                  {...register('rememberMe')}
                  className="rounded bg-slate-950 border-slate-800 text-indigo-600 focus:ring-indigo-500"
                />
                <span>Remember me on this device</span>
              </label>
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full bg-indigo-600 hover:bg-indigo-500 text-white font-semibold py-3 px-4 rounded-xl text-sm transition-colors flex items-center justify-center gap-2 shadow-lg shadow-indigo-600/30 disabled:opacity-50 mt-2"
            >
              {isSubmitting ? 'Authenticating...' : 'Sign In'}
              <ArrowRight className="w-4 h-4" />
            </button>
          </form>

          {/* Quick Demo Credentials Help */}
          <div className="pt-4 border-t border-slate-800/80 text-center text-xs text-slate-500 space-y-1">
            <p>Demo Login: <code className="text-indigo-400">devs@acme.com</code></p>
            <p>Password: <code className="text-indigo-400">SecretPassword123!</code></p>
          </div>
        </div>
      </div>
    </div>
  );
};
