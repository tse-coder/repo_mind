import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'RepoMind — Autonomous Local Repository Investigation Agent',
  description: 'Investigate repositories with verifiable line citations powered by LangGraph & Gemini.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-[#090d16] text-[#e6edf3] antialiased">
        {children}
      </body>
    </html>
  );
}

