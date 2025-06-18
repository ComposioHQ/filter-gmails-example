interface ConnectionResponse {
  connection_id: string
  redirect_url: string
  status: 'active' | 'initiated' | 'failed' | 'expired' | 'deleted'
}

interface ConnectionStatusResponse {
  user_id: string
  status: 'active' | 'initiated' | 'failed' | 'expired' | 'deleted'
  connected: boolean
  connection_id: string | null
  account_id: string | null
  app_name: string | null
  created_at: string | null
  error_message: string | null
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export async function createConnection(userId: string): Promise<ConnectionResponse> {
  const response = await fetch(`${API_URL}/api/connection`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ user_id: userId }),
  })

  if (!response.ok) {
    throw new Error(`Failed to create connection: ${response.statusText}`)
  }

  return response.json()
}

export async function checkConnectionStatus(nanoId: string): Promise<ConnectionStatusResponse> {
  const response = await fetch(`${API_URL}/api/connection/?nano_id=${nanoId}`)

  if (!response.ok) {
    throw new Error(`Failed to check connection status: ${response.statusText}`)
  }

  return response.json()
}