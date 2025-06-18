'use client'

import { useEffect, useState, useCallback } from 'react'
import { createClient } from '@/lib/supabase/client'
import { checkConnectionStatus } from '@/lib/api'
import type { Database } from '@/lib/supabase/database.types'

type Connection = Database['public']['Tables']['connections']['Row']

interface UseConnectionReturn {
  connection: Connection | null
  isLoading: boolean
  isActive: boolean
  error: string | null
  refetch: () => Promise<void>
}

export function useConnection(userId: string): UseConnectionReturn {
  const [connection, setConnection] = useState<Connection | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isActive, setIsActive] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const supabase = createClient()

  const fetchConnection = useCallback(async () => {
    try {
      setIsLoading(true)
      setError(null)

      // First, check if user has a connection in Supabase
      const { data, error: supabaseError } = await supabase
        .from('connections')
        .select('*')
        .eq('user_id', userId)
        .single()

      if (supabaseError && supabaseError.code !== 'PGRST116') {
        throw new Error('Failed to fetch connection')
      }

      if (data) {
        setConnection(data)
        
        // Check the actual status from Composio
        try {
          const status = await checkConnectionStatus(data.connected_account_id)
          
          // Update status in Supabase if it changed
          if (status.status !== data.connection_status) {
            await supabase
              .from('connections')
              .update({ connection_status: status.status })
              .eq('id', data.id)
          }
          
          setIsActive(status.status === 'active')
          setConnection({ ...data, connection_status: status.status })
        } catch (err) {
          console.error('Failed to check connection status:', err)
          setIsActive(data.connection_status === 'active')
        }
      } else {
        setConnection(null)
        setIsActive(false)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred')
      setIsActive(false)
    } finally {
      setIsLoading(false)
    }
  }, [userId, supabase])

  useEffect(() => {
    fetchConnection()
  }, [fetchConnection])

  // Poll for status if connection is initiated
  useEffect(() => {
    if (connection?.connection_status === 'initiated') {
      const interval = setInterval(async () => {
        try {
          const status = await checkConnectionStatus(connection.connected_account_id)
          
          if (status.status !== 'initiated') {
            // Update status in Supabase
            await supabase
              .from('connections')
              .update({ connection_status: status.status })
              .eq('id', connection.id)
            
            setConnection({ ...connection, connection_status: status.status })
            setIsActive(status.status === 'active')
            
            // Stop polling if status changed
            clearInterval(interval)
          }
        } catch (err) {
          console.error('Polling error:', err)
        }
      }, 2000) // Poll every 2 seconds

      return () => clearInterval(interval)
    }
  }, [connection, supabase])

  return {
    connection,
    isLoading,
    isActive,
    error,
    refetch: fetchConnection,
  }
}