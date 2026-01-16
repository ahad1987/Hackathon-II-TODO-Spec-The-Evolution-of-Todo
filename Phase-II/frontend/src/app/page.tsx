/**
 * Root page - Landing page with redirect to tasks if authenticated.
 */

'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth-context';
import Link from 'next/link';

export default function Home() {
  const router = useRouter();
  const { isAuthenticated, isLoading } = useAuth();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (mounted && !isLoading) {
      if (isAuthenticated) {
        router.push('/tasks');
      } else {
        // Show landing page for non-authenticated users
      }
    }
  }, [isAuthenticated, isLoading, mounted, router]);

  if (!mounted || isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-pulse">
            <div className="h-12 w-12 bg-blue-600 rounded-lg mx-auto mb-4"></div>
            <p className="text-slate-600">Loading...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50">
      {/* Navigation */}
      <nav className="fixed top-0 w-full bg-white/80 backdrop-blur-md border-b border-slate-100 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 bg-gradient-to-br from-blue-600 to-blue-700 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-lg">✓</span>
              </div>
              <span className="text-xl font-bold text-slate-900">TaskFlow</span>
            </div>
            <div className="flex gap-3">
              <Link href="/login" className="px-4 py-2 text-slate-600 hover:text-slate-900 transition-colors">
                Sign In
              </Link>
              <Link href="/signup" className="btn-primary">
                Get Started
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <div className="pt-32 pb-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-4xl mx-auto text-center">
          {/* Badge */}
          <div className="inline-flex items-center gap-2 px-4 py-2 bg-blue-50 border border-blue-200 rounded-full mb-6">
            <span className="w-2 h-2 bg-blue-600 rounded-full"></span>
            <span className="text-sm font-medium text-blue-900">Introducing TaskFlow v1.0</span>
          </div>

          {/* Main Headline */}
          <h1 className="text-5xl sm:text-6xl font-bold text-slate-900 mb-6 leading-tight">
            Organize. Prioritize.<br />
            <span className="bg-gradient-to-r from-blue-600 to-blue-700 text-transparent bg-clip-text">Accomplish.</span>
          </h1>

          {/* Subheading */}
          <p className="text-xl text-slate-600 mb-8 max-w-2xl mx-auto">
            Now powered by AI — manage your tasks through natural conversation. TaskFlow helps you create, organize, and complete tasks effortlessly. Stay focused on what matters most.
          </p>

          {/* CTA Buttons */}
          <div className="flex flex-col sm:flex-row gap-4 justify-center mb-12">
            <Link href="/signup" className="btn-primary text-lg px-8 py-3">
              Start Free with AI
            </Link>
            <Link
              href="/login"
              className="px-8 py-3 bg-slate-200 text-slate-900 font-medium rounded-lg hover:bg-slate-300 transition-colors text-lg"
            >
              Sign In
            </Link>
          </div>

          {/* Trust Indicators */}
          <p className="text-sm text-slate-500">
            No credit card required • Start in seconds • Completely secure
          </p>
        </div>
      </div>

      {/* Features Section */}
      <div className="py-20 px-4 sm:px-6 lg:px-8 bg-white/40">
        <div className="max-w-5xl mx-auto">
          <h2 className="text-4xl font-bold text-center text-slate-900 mb-16">
            Everything you need to succeed
          </h2>

          <div className="grid md:grid-cols-3 gap-8">
            {/* Feature 1 */}
            <div className="card p-8">
              <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mb-4">
                <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                </svg>
              </div>
              <h3 className="text-lg font-semibold text-slate-900 mb-2">Simple Task Management</h3>
              <p className="text-slate-600">Create, edit, and organize your tasks with an intuitive interface designed for productivity.</p>
            </div>

            {/* Feature 2 */}
            <div className="card p-8">
              <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mb-4">
                <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m7 8a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <h3 className="text-lg font-semibold text-slate-900 mb-2">Track Progress</h3>
              <p className="text-slate-600">Monitor your completed and pending tasks with real-time statistics and insights.</p>
            </div>

            {/* Feature 3 */}
            <div className="card p-8">
              <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mb-4">
                <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                </svg>
              </div>
              <h3 className="text-lg font-semibold text-slate-900 mb-2">Secure & Private</h3>
              <p className="text-slate-600">Your data is encrypted and secure. Only you can access your tasks and information.</p>
            </div>
          </div>
        </div>
      </div>

      {/* Footer CTA */}
      <div className="py-16 px-4 sm:px-6 lg:px-8">
        <div className="max-w-3xl mx-auto text-center">
          <h2 className="text-3xl font-bold text-slate-900 mb-6">Ready to boost your productivity?</h2>
          <Link href="/signup" className="btn-primary text-lg px-8 py-3 inline-block">
            Create Free Account
          </Link>
        </div>
      </div>

      {/* Footer */}
      <footer className="border-t border-slate-100 bg-white/50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="flex justify-between items-center">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 bg-gradient-to-br from-blue-600 to-blue-700 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold">✓</span>
              </div>
              <span className="font-semibold text-slate-900">TaskFlow</span>
            </div>
            <p className="text-sm text-slate-600">© 2026 TaskFlow. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </div>
  );
}
