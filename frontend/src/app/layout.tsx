import type { Metadata } from 'next';
import './globals.css';
import { Providers } from "@/components/providers";

export const metadata: Metadata = {
  title: 'RepoMind — Repository Investigation Agent',
  description: 'Investigate repositories with verifiable line citations.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-slate-50 text-slate-900 antialiased font-sans">
        <Providers>
          {children}
        </Providers>
      </body>
    </html>
  );
}
