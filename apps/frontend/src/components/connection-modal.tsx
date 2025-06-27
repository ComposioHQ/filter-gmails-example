"use client";

import { useState, useEffect, useRef } from "react";
import { createConnection, checkConnectionStatus } from "@/lib/api";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Loader2, Mail, CheckCircle } from "lucide-react";

interface ConnectionModalProps {
  userId: string;
  open: boolean;
  onConnectionComplete: () => void;
}

export function ConnectionModal({
  userId,
  open,
  onConnectionComplete,
}: ConnectionModalProps) {
  const [isConnecting, setIsConnecting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [connectionId, setConnectionId] = useState<string | null>(null);
  const [isPolling, setIsPolling] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<string | null>(null);
  const pollingInterval = useRef<NodeJS.Timeout | null>(null);

  const handleConnect = async () => {
    try {
      setIsConnecting(true);
      setError(null);

      // Create connection via API (handles both Composio and Supabase)
      const { connection_id, redirect_url } =
        await createConnection(userId);

      setConnectionId(connection_id);

      // Open in new tab
      window.open(redirect_url, "_blank", "noopener,noreferrer");

      // Start polling for connection status
      setIsPolling(true);
      setConnectionStatus("INITIATED");
    } catch (err) {
      console.error("Connection error:", err);
      setError(err instanceof Error ? err.message : "Failed to connect Gmail");
      setIsConnecting(false);
    }
  };

  // Reset states when modal closes
  useEffect(() => {
    if (!open) {
      setIsConnecting(false);
      setIsPolling(false);
      setConnectionStatus(null);
      setConnectionId(null);
      setError(null);
    }
  }, [open]);

  // Polling effect
  useEffect(() => {
    if (!isPolling || !connectionId) return;

    const checkStatus = async () => {
      try {
        const status = await checkConnectionStatus(connectionId);
        setConnectionStatus(status.status);

        if (status.status === "ACTIVE") {
          setIsPolling(false);
          setIsConnecting(false);
          // Wait a moment to show success state, then call completion
          setTimeout(() => {
            onConnectionComplete();
          }, 1500);
        } else if (status.status === "FAILED") {
          setIsPolling(false);
          setIsConnecting(false);
          setError("Connection failed. Please try again.");
        }
        // Continue polling if status is "INITIATED"
      } catch (err) {
        console.error("Error checking connection status:", err);
        // Don't show error immediately, just continue polling
        // The connection might still be initializing
      }
    };

    // Initial check
    checkStatus();

    // Set up polling interval
    pollingInterval.current = setInterval(checkStatus, 2000);

    return () => {
      if (pollingInterval.current) {
        clearInterval(pollingInterval.current);
      }
    };
  }, [isPolling, connectionId, onConnectionComplete]);

  return (
    <Dialog open={open}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Mail className="size-5" />
            Connect Your Gmail Account
          </DialogTitle>
          <DialogDescription>
            {connectionStatus === "ACTIVE" ? (
              "Your Gmail account is successfully connected!"
            ) : (
              "Connect your Gmail account to start using AI-powered email labelling. Your emails will be automatically categorized based on your custom prompts."
            )}
          </DialogDescription>
        </DialogHeader>

        <div className="mt-6 space-y-4">
          {error && (
            <div className="p-3 text-sm text-destructive bg-destructive/10 rounded-md">
              {error}
            </div>
          )}

          {connectionStatus === "active" ? (
            <div className="flex flex-col items-center space-y-4">
              <CheckCircle className="size-16 text-green-500" />
              <p className="text-center text-sm text-muted-foreground">
                Gmail connected successfully! Redirecting...
              </p>
            </div>
          ) : (
            <>
              <Button
                onClick={handleConnect}
                disabled={isConnecting || isPolling}
                className="w-full"
                size="lg"
              >
                {isPolling ? (
                  <>
                    <Loader2 className="mr-2 size-4 animate-spin" />
                    Waiting for authorization...
                  </>
                ) : isConnecting ? (
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

              {isPolling && (
                <p className="text-xs text-center text-muted-foreground">
                  Please complete the authorization in the new tab. We&apos;re
                  checking the connection status...
                </p>
              )}

              {!isPolling && !isConnecting && (
                <p className="text-xs text-center text-muted-foreground">
                  You&apos;ll be redirected to Google to authorize access. We only
                  request permissions to read and label your emails.
                </p>
              )}
            </>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
