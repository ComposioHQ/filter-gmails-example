import { redirect } from 'next/navigation'
import { createClient } from '@/lib/supabase/server'
import { HomeContent } from './home-content'

export default async function Home() {
  const supabase = await createClient()

  const { data, error } = await supabase.auth.getUser()
  if (error || !data?.user) {
    redirect('/auth/login')
  }

  return <HomeContent user={data.user} />
}