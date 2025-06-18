'use client'

import { useEffect, useState, useCallback, useRef } from 'react'
import { createClient } from '@/lib/supabase/client'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Loader2 } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { Database } from '@/lib/supabase/database.types'

type Prompt = Database['public']['Tables']['prompts']['Row']

interface PromptEditorProps {
  userId: string
  disabled?: boolean
}

export function PromptEditor({ userId, disabled = false }: PromptEditorProps) {
  const [prompt, setPrompt] = useState<Prompt | null>(null)
  const [classification, setClassification] = useState('')
  const [bio, setBio] = useState('')
  const [preferences, setPreferences] = useState('')
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [saveStatus, setSaveStatus] = useState<'idle' | 'success' | 'error'>('idle')
  
  const classificationRef = useRef<HTMLTextAreaElement>(null)
  const bioRef = useRef<HTMLTextAreaElement>(null)
  const preferencesRef = useRef<HTMLTextAreaElement>(null)
  
  const supabase = createClient()

  const fetchPrompt = useCallback(async () => {
    setIsLoading(true)
    try {
      const { data, error } = await supabase
        .from('prompts')
        .select('*')
        .eq('user_id', userId)
        .single()

      if (error && error.code !== 'PGRST116') {
        console.error('Error fetching prompt:', error)
      } else if (data) {
        setPrompt(data)
        // Split the prompt into sections
        const sections = data.prompt.split('\n\n')
        if (sections.length >= 3) {
          // Extract classification after "Please classify this email as either: "
          const classSection = sections[0] || ''
          setClassification(classSection.replace(/^Please classify this email as either:\s*/, ''))
          // Extract bio after "My basic bio: "
          const bioSection = sections[1] || ''
          setBio(bioSection.replace(/^My basic bio:\s*/, ''))
          // Extract preferences after "Some context on my preferences: "
          const prefsSection = sections.slice(2).join('\n\n') || ''
          setPreferences(prefsSection.replace(/^Some context on my preferences:\s*/, ''))
        } else {
          // If prompt doesn't have proper sections, put everything in classification
          setClassification(data.prompt)
        }
      }
    } finally {
      setIsLoading(false)
    }
  }, [userId, supabase])

  useEffect(() => {
    fetchPrompt()
  }, [fetchPrompt])

  // Simple change handler without auto-resize
  const handleTextareaChange = (
    e: React.ChangeEvent<HTMLTextAreaElement>, 
    setter: (value: string) => void
  ) => {
    setter(e.target.value)
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>, nextAction: 'bio' | 'preferences' | 'save') => {
    if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
      e.preventDefault()
      switch(nextAction) {
        case 'bio':
          bioRef.current?.focus()
          break
        case 'preferences':
          preferencesRef.current?.focus()
          break
        case 'save':
          handleSave()
          break
      }
    }
  }

  const handleSave = async () => {
    setIsSaving(true)
    setSaveStatus('idle')

    // Concatenate all sections with headers
    const fullPrompt = `Please classify this email as either: ${classification}\n\nMy basic bio: ${bio}\n\nSome context on my preferences: ${preferences}`.trim()

    try {
      if (prompt) {
        const { error } = await supabase
          .from('prompts')
          .update({ 
            prompt: fullPrompt,
            updated_at: new Date().toISOString()
          })
          .eq('id', prompt.id)

        if (error) throw error
      } else {
        const { data, error } = await supabase
          .from('prompts')
          .insert({ 
            user_id: userId,
            prompt: fullPrompt
          })
          .select()
          .single()

        if (error) throw error
        setPrompt(data)
      }

      setSaveStatus('success')
      setTimeout(() => setSaveStatus('idle'), 2000)
    } catch (error) {
      console.error('Error saving prompt:', error)
      setSaveStatus('error')
      setTimeout(() => setSaveStatus('idle'), 3000)
    } finally {
      setIsSaving(false)
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="size-8 animate-spin text-muted-foreground" />
      </div>
    )
  }

  return (
    <Card className={cn("w-full max-w-4xl mx-auto max-h-[800px] flex flex-col", disabled && "opacity-50")}>
      <CardHeader className="flex-shrink-0">
        <CardTitle>AI Agent Prompt</CardTitle>
        <CardDescription>
          {disabled ? 'Connect your Gmail account to start training your AI agent.' : 'Train your AI agent to automatically label your Gmail inbox by providing context in three sections.'}
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6 overflow-y-auto flex-1 pb-0">
        <div className="space-y-4">
          <div className="space-y-2">
            <label className="text-sm font-medium">Please classify this email as either:</label>
            <Textarea
              ref={classificationRef}
              value={classification}
              onChange={(e) => handleTextareaChange(e, setClassification)}
              onKeyDown={(e) => handleKeyDown(e, 'bio')}
              placeholder="Important, Personal, Newsletters, Work, Spam..."
              className="h-[200px] font-mono text-sm resize-none overflow-y-auto"
              aria-label="Email classification categories"
              disabled={disabled}
            />
            <span className="text-xs text-muted-foreground">Press Cmd+Enter to continue</span>
          </div>
          
          <div className="space-y-2">
            <label className="text-sm font-medium">My basic bio:</label>
            <Textarea
              ref={bioRef}
              value={bio}
              onChange={(e) => handleTextareaChange(e, setBio)}
              onKeyDown={(e) => handleKeyDown(e, 'preferences')}
              placeholder="I'm a software engineer working at..."
              className="h-[200px] font-mono text-sm resize-none overflow-y-auto"
              aria-label="Your basic bio"
              disabled={disabled}
            />
            <span className="text-xs text-muted-foreground">Press Cmd+Enter to continue</span>
          </div>
          
          <div className="space-y-2">
            <label className="text-sm font-medium">Some context on my preferences:</label>
            <Textarea
              ref={preferencesRef}
              value={preferences}
              onChange={(e) => handleTextareaChange(e, setPreferences)}
              onKeyDown={(e) => handleKeyDown(e, 'save')}
              placeholder="I prefer concise emails, I'm interested in tech news..."
              className="h-[200px] font-mono text-sm resize-none overflow-y-auto"
              aria-label="Your email preferences"
              disabled={disabled}
            />
            <span className="text-xs text-muted-foreground">Press Cmd+Enter to save</span>
          </div>
        </div>
      </CardContent>
      <div className="border-t p-4 flex-shrink-0 flex items-center justify-end bg-muted/30">
        <div className="flex items-center gap-2">
          {saveStatus === 'success' && (
            <span className="text-xs text-green-600">Saved successfully!</span>
          )}
          {saveStatus === 'error' && (
            <span className="text-xs text-destructive">Error saving. Please try again.</span>
          )}
          <Button 
            onClick={handleSave} 
            disabled={disabled || isSaving || (!classification.trim() && !bio.trim() && !preferences.trim())}
            className=""
          >
            {isSaving ? (
              <>
                <Loader2 className="mr-2 size-4 animate-spin" />
                Saving...
              </>
            ) : (
              prompt ? 'Update Prompt' : 'Save Prompt'
            )}
          </Button>
        </div>
      </div>
    </Card>
  )
}