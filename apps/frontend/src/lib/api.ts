// Connection status values from Composio API
type ComposioConnectionStatus = 'INITIATED' | 'ACTIVE' | 'FAILED' | 'EXPIRED' | 'REVOKED'

interface ConnectionResponse {
  connection_id: string
  redirect_url: string
  status: ComposioConnectionStatus
}

interface ConnectionStatusResponse {
  user_id: string
  status: ComposioConnectionStatus
  connected: boolean
  connection_id: string | null
  account_id: string | null
  app_name: string | null
  created_at: string | null
  error_message: string | null
}

export async function createConnection(userId: string): Promise<ConnectionResponse> {
  const response = await fetch('/api/connections', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ user_id: userId }),
  })

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.error || `Failed to create connection: ${response.statusText}`)
  }

  return response.json()
}

export async function checkConnectionStatus(nanoId: string): Promise<ConnectionStatusResponse> {
  const response = await fetch(`/api/connections?nano_id=${nanoId}`)

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.error || `Failed to check connection status: ${response.statusText}`)
  }

  return response.json()
}