"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useSession, signOut } from "@/lib/auth-client";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogTrigger } from "@/components/ui/dialog";
import { Auth } from "@/components/auth/auth";
import { LogOut, LogIn } from "lucide-react";

export function UserNav() {
  const { data: session, isPending } = useSession();
  const [modalOpen, setModalOpen] = useState(false);

  if (isPending) {
    return (
      <div className="w-8 h-8 rounded-full bg-slate-100 animate-pulse border border-slate-200" />
    );
  }

  if (!session?.user) {
    return (
      <Dialog open={modalOpen} onOpenChange={setModalOpen}>
        <DialogTrigger render={
          <Button
            variant="outline"
            size="sm"
            className="h-8 gap-1.5 text-xs font-medium text-slate-700 hover:text-slate-900 border-slate-200 bg-white shadow-xs"
          >
            <LogIn className="w-3.5 h-3.5" />
            Sign in
          </Button>
        } />
        <DialogContent className="max-w-md p-0 overflow-hidden border-slate-200 bg-white">
          <div className="p-4 bg-slate-50/80 border-b border-slate-100">
            <h3 className="font-semibold text-slate-900 text-sm">RepoMind Authentication</h3>
            <p className="text-xs text-slate-500 mt-0.5">
              Sign in with username/password or Google to sync investigations and checkpoints.
            </p>
          </div>
          <div className="p-4 max-h-[80vh] overflow-y-auto">
            <Auth view="signIn" className="border-0 shadow-none p-0" />
          </div>
        </DialogContent>
      </Dialog>
    );
  }

  const user = session.user;
  const initials = (user.name || user.email || "U")
    .split(" ")
    .map((n: string) => n[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();

  return (
    <DropdownMenu>
      <DropdownMenuTrigger render={
        <button
          type="button"
          aria-label="User profile"
          className="rounded-full ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500 focus-visible:ring-offset-2 hover:opacity-90 cursor-pointer"
        >
          <Avatar className="h-8 w-8 border border-slate-200">
            {user.image && <AvatarImage src={user.image} alt={user.name || "User"} />}
            <AvatarFallback className="bg-indigo-50 text-indigo-700 font-medium text-xs">
              {initials}
            </AvatarFallback>
          </Avatar>
        </button>
      } />
      <DropdownMenuContent align="end" className="w-56 bg-white border-slate-200">
        <div className="p-2">
          <p className="text-xs font-semibold text-slate-900 leading-none">{user.name || "User"}</p>
          <p className="text-[11px] text-slate-500 leading-none mt-1 truncate">
            {user.email}
          </p>
          {user.username && (
            <p className="text-[10px] text-slate-400 font-mono mt-0.5 truncate">
              @{user.username}
            </p>
          )}
        </div>
        <DropdownMenuSeparator className="bg-slate-100" />
        <DropdownMenuItem
          className="cursor-pointer text-xs text-red-600 focus:text-red-700 focus:bg-red-50 gap-2 px-2 py-1.5 rounded-md"
          onClick={() => signOut()}
        >
          <LogOut className="w-3.5 h-3.5" />
          Sign out
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
