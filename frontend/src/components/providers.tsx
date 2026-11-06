"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { AuthProvider } from "@/components/auth/auth-provider";
import { authClient } from "@/lib/auth-client";
import { TooltipProvider } from "@/components/ui/tooltip";
import Link from "next/link";

export function Providers({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 1000 * 60 * 5,
            refetchOnWindowFocus: false,
          },
        },
      })
  );

  const handleNavigate = ({ to, replace }: { to: string; replace?: boolean }) => {
    if (replace) {
      router.replace(to);
    } else {
      router.push(to);
    }
  };

  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider
        authClient={authClient}
        navigate={handleNavigate}
        Link={Link as any}
      >
        <TooltipProvider delay={200}>
          {children}
        </TooltipProvider>
      </AuthProvider>
    </QueryClientProvider>
  );
}
