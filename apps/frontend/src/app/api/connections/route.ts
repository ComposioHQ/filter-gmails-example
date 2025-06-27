import { NextRequest, NextResponse } from 'next/server'
import { createClient } from '@/lib/supabase/server'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export async function POST(request: NextRequest) {
  try {
    // Get the request body
    const body = await request.json()
    const { user_id } = body

    if (!user_id) {
      return NextResponse.json(
        { error: 'user_id is required' },
        { status: 400 }
      )
    }

    // Create server-side Supabase client
    const supabase = await createClient()

    // Verify the user is authenticated and matches the requested user_id
    const { data: { user }, error: authError } = await supabase.auth.getUser()
    
    if (authError || !user) {
      return NextResponse.json(
        { error: 'Unauthorized' },
        { status: 401 }
      )
    }

    if (user.id !== user_id) {
      return NextResponse.json(
        { error: 'User ID mismatch' },
        { status: 403 }
      )
    }

    // Call Python backend to initiate Composio connection
    const composioResponse = await fetch(`${API_URL}/api/connection`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ user_id }),
    })

    if (!composioResponse.ok) {
      const errorText = await composioResponse.text()
      throw new Error(`Failed to create Composio connection: ${errorText}`)
    }

    const composioData = await composioResponse.json()

    // Save connection to Supabase using server client (with proper auth context)
    const { error: supabaseError } = await supabase
      .from('connections')
      .insert({
        user_id: user_id,
        connected_account_id: composioData.connection_id,
        connection_status: 'initiated',
      })

    if (supabaseError) {
      console.error('Supabase error saving connection:', supabaseError)
      throw new Error(`Failed to save connection: ${supabaseError.message}`)
    }

    // Return the connection data
    return NextResponse.json({
      connection_id: composioData.connection_id,
      redirect_url: composioData.redirect_url,
      status: composioData.status,
    })

  } catch (error) {
    console.error('Connection error:', error)
    return NextResponse.json(
      { error: error instanceof Error ? error.message : 'Failed to create connection' },
      { status: 500 }
    )
  }
}

export async function GET(request: NextRequest) {
  try {
    // Get nano_id from query params
    const searchParams = request.nextUrl.searchParams
    const nano_id = searchParams.get('nano_id')

    if (!nano_id) {
      return NextResponse.json(
        { error: 'nano_id is required' },
        { status: 400 }
      )
    }

    // Create server-side Supabase client
    const supabase = await createClient()

    // Verify the user is authenticated
    const { data: { user }, error: authError } = await supabase.auth.getUser()
    
    if (authError || !user) {
      return NextResponse.json(
        { error: 'Unauthorized' },
        { status: 401 }
      )
    }

    // Call Python backend to check connection status
    const response = await fetch(`${API_URL}/api/connection/?nano_id=${nano_id}`)

    if (!response.ok) {
      throw new Error(`Failed to check connection status: ${response.statusText}`)
    }

    const data = await response.json()

    // For now, just return the data without user verification
    // as the connection might still be initializing
    return NextResponse.json(data)

  } catch (error) {
    console.error('Connection status error:', error)
    return NextResponse.json(
      { error: error instanceof Error ? error.message : 'Failed to check connection status' },
      { status: 500 }
    )
  }
}