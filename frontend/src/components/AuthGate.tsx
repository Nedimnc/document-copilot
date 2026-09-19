import { useEffect, useState, type ReactNode } from "react"
import { Navigate } from "react-router-dom"

import { supabase } from "@/lib/supabase"

export function AuthGate({ children }: { children: ReactNode }) {
  const [ready, setReady] = useState(false)
  const [signedIn, setSignedIn] = useState(false)

  useEffect(() => {
    let cancelled = false

    supabase.auth.getSession().then(({ data }) => {
      if (!cancelled) {
        setSignedIn(data.session !== null)
        setReady(true)
      }
    })

    const { data } = supabase.auth.onAuthStateChange((_event, session) => {
      setSignedIn(session !== null)
      setReady(true)
    })

    return () => {
      cancelled = true
      data.subscription.unsubscribe()
    }
  }, [])

  if (!ready) {
    return (
      <main className="flex min-h-svh items-center justify-center text-zinc-500">
        Loading…
      </main>
    )
  }

  if (!signedIn) {
    return <Navigate to="/login" replace />
  }

  return children
}
