'use client'

import { LogoutButton } from '@/components/logout-button'
import { PromptEditor } from '@/components/prompt-editor'
import { ConnectionModal } from '@/components/connection-modal'
import { Card, CardContent } from '@/components/ui/card'
import { useConnection } from '@/hooks/use-connection'
import { Loader2 } from 'lucide-react'
import type { User } from '@supabase/supabase-js'

interface HomeContentProps {
  user: User
}

export function HomeContent({ user }: HomeContentProps) {
  const { connection, isLoading, isActive, refetch } = useConnection(user.id)

  if (isLoading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <Loader2 className="size-8 animate-spin text-muted-foreground" />
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <div className="text-sm text-muted-foreground">
            {user.email}
          </div>
          <div className="flex items-center gap-4">
            {isActive && (
              <span className="text-xs text-green-600 dark:text-green-400 flex items-center gap-1">
                <span className="size-2 rounded-full bg-green-600 dark:bg-green-400" />
                Gmail Connected
              </span>
            )}
            <LogoutButton />
          </div>
        </div>
      </header>
      
      <main className="container mx-auto px-4 py-12">
        <div className="max-w-4xl mx-auto space-y-8">
          <div className="text-center space-y-2">
            <h1 className="text-4xl font-bold tracking-tight">Gmail Reaper</h1>
            <p className="text-muted-foreground">
              Train your AI agent to automatically label your Gmail inbox
            </p>
          </div>
          
          <PromptEditor 
            userId={user.id} 
            disabled={process.env.NEXT_PUBLIC_ENABLE_CONNECTION_MODAL === 'true' ? !isActive : false} 
          />
          
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <Card className="cursor-pointer transition-all hover:scale-105 hover:shadow-lg border-red-200 dark:border-red-900 bg-red-50 dark:bg-red-950/20">
              <CardContent className="p-6 text-center">
                <h3 className="font-semibold text-red-700 dark:text-red-400">Send spam email</h3>
              </CardContent>
            </Card>
            
            <Card className="cursor-pointer transition-all hover:scale-105 hover:shadow-lg border-green-200 dark:border-green-900 bg-green-50 dark:bg-green-950/20">
              <CardContent className="p-6 text-center">
                <h3 className="font-semibold text-green-700 dark:text-green-400">Send cool email</h3>
              </CardContent>
            </Card>
            
            <Card className="cursor-pointer transition-all hover:scale-105 hover:shadow-lg border-blue-200 dark:border-blue-900 bg-blue-50 dark:bg-blue-950/20">
              <CardContent className="p-6 text-center">
                <h3 className="font-semibold text-blue-700 dark:text-blue-400">Send marketing email</h3>
              </CardContent>
            </Card>
          </div>
        </div>
      </main>
      
      {process.env.NEXT_PUBLIC_ENABLE_CONNECTION_MODAL === 'true' && (
        <ConnectionModal 
          userId={user.id} 
          open={!isActive && !connection?.connection_status} 
          onConnectionComplete={refetch}
        />
      )}
    </div>
  )
}