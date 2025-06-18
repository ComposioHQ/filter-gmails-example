'use client'

import { useState } from 'react'
import { createClient } from '@/lib/supabase/client'
import { createConnection } from '@/lib/api'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Loader2, Mail } from 'lucide-react'

interface ConnectionModalProps {
  userId: string
  open: boolean
  onConnectionComplete: () => void
}

export function ConnectionModal({ userId, open, onConnectionComplete }: ConnectionModalProps) {
  const [isConnecting, setIsConnecting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  
  const supabase = createClient()

  const handleConnect = async () => {
    try {
      setIsConnecting(true)
      setError(null)

      // Create connection via API
      const { connection_id, redirect_url } = await createConnection(userId)

      // Save connection to Supabase
      const { error: supabaseError } = await supabase
        .from('connections')
        .insert({
          user_id: userId,
          connected_account_id: connection_id,
          connection_status: 'initiated',
        })

      if (supabaseError) {
        throw new Error('Failed to save connection')
      }

      // Try to open in new tab
      const newWindow = window.open(redirect_url, '_blank', 'noopener,noreferrer')
      
      // If popup was blocked, redirect in same tab
      if (!newWindow || newWindow.closed || typeof newWindow.closed === 'undefined') {
        window.location.href = redirect_url
      } else {
        // Start polling for connection status
        onConnectionComplete()
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to connect Gmail')
      setIsConnecting(false)
    }
  }

  return (
    <Dialog open={open}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Mail className="size-5" />
            Connect Your Gmail Account
          </DialogTitle>
          <DialogDescription>
            Connect your Gmail account to start using AI-powered email labelling. Your emails will be automatically categorized based on your custom prompts.
          </DialogDescription>
        </DialogHeader>
        
        <div className="mt-6 space-y-4">
          {error && (
            <div className="p-3 text-sm text-destructive bg-destructive/10 rounded-md">
              {error}
            </div>
          )}
          
          <Button 
            onClick={handleConnect} 
            disabled={isConnecting}
            className="w-full"
            size="lg"
          >
            {isConnecting ? (
              <>
                <Loader2 className="mr-2 size-4 animate-spin" />
                Connecting...
              </>
            ) : (
              <>
                <Mail className="mr-2 size-4" />
                Connect Gmail!
              </>
            )}
          </Button>
          
          <p className="text-xs text-center text-muted-foreground">
            You&apos;ll be redirected to Google to authorize access. We only request permissions to read and label your emails.
          </p>
        </div>
      </DialogContent>
    </Dialog>
  )
}