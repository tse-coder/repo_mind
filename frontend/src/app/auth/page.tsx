"use client";

import { Auth } from "@/components/auth/auth";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";

export default function AuthPage() {
  return (
    <div className="min-h-screen bg-slate-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <Link
          href="/"
          className="inline-flex items-center text-sm font-medium text-slate-500 hover:text-slate-800 mb-6 transition-colors"
        >
          <ArrowLeft className="w-4 h-4 mr-1" />
          Back to RepoMind
        </Link>
        <div className="flex items-center space-x-3 mb-2">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-indigo-600 to-violet-500 flex items-center justify-center shadow-md shadow-indigo-500/20">
            <span className="font-bold text-white text-lg">R</span>
          </div>
          <span className="text-xl font-bold tracking-tight text-slate-900">
            RepoMind
          </span>
        </div>
        <p className="text-sm text-slate-500 mb-6">
          Sign in or create an account to persist investigation threads and repository insights.
        </p>
      </div>

      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <Auth view="signIn" className="shadow-sm border border-slate-200/80 rounded-xl bg-white" />
      </div>
    </div>
  );
}
