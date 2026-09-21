import { FileText } from "lucide-react"
import { useEffect, useState, type FormEvent } from "react"
import { Navigate } from "react-router-dom"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { signIn, signUp } from "@/lib/auth"
import { supabase } from "@/lib/supabase"

type Mode = "signin" | "signup"

function errorMessage(error: unknown): string {
  if (error && typeof error === "object" && "message" in error) {
    const message = error.message
    if (typeof message === "string" && message.trim()) {
      return message
    }
  }
  return "Something went wrong. Try again."
}

export function LoginPage() {
  const [mode, setMode] = useState<Mode>("signin")
  const [error, setError] = useState<string | null>(null)
  const [notice, setNotice] = useState<string | null>(null)
  const [pending, setPending] = useState(false)
  const [signedIn, setSignedIn] = useState(false)

  useEffect(() => {
    supabase.auth.getSession().then(({ data }) => {
      if (data.session) {
        setSignedIn(true)
      }
    })
  }, [])

  if (signedIn) {
    return <Navigate to="/" replace />
  }

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const form = new FormData(event.currentTarget)
    const email = String(form.get("email") ?? "").trim()
    const password = String(form.get("password") ?? "")

    setError(null)
    setNotice(null)
    setPending(true)

    try {
      if (mode === "signin") {
        await signIn(email, password)
        setSignedIn(true)
        return
      }

      const result = await signUp(email, password)
      if (result.session) {
        setSignedIn(true)
        return
      }
      setNotice(
        "Account created. Confirm the email in Supabase Auth if confirmation is enabled, then sign in.",
      )
    } catch (caught) {
      setError(errorMessage(caught))
    } finally {
      setPending(false)
    }
  }

  return (
    <main className="flex min-h-svh items-center justify-center px-4">
      <div className="w-full max-w-sm rounded-xl border bg-card p-6 shadow-sm">
        <div className="flex items-center gap-2.5">
          <div className="flex size-9 items-center justify-center rounded-md bg-primary text-primary-foreground">
            <FileText className="size-4.5" />
          </div>
          <div>
            <h1 className="text-base font-semibold leading-tight">Document Copilot</h1>
            <p className="text-xs text-muted-foreground">Driftwood Capital</p>
          </div>
        </div>

        <p className="mt-5 text-sm text-muted-foreground">
          {mode === "signin"
            ? "Sign in with your Driftwood email."
            : "Create an account with your Driftwood email."}
        </p>

        <form className="mt-4 space-y-4" onSubmit={onSubmit}>
          <div className="space-y-1.5">
            <label htmlFor="email" className="text-sm font-medium">
              Email
            </label>
            <Input id="email" name="email" type="email" autoComplete="email" required />
          </div>
          <div className="space-y-1.5">
            <label htmlFor="password" className="text-sm font-medium">
              Password
            </label>
            <Input
              id="password"
              name="password"
              type="password"
              autoComplete={mode === "signin" ? "current-password" : "new-password"}
              minLength={6}
              required
            />
          </div>

          {error ? (
            <p className="text-sm text-destructive" role="alert">
              {error}
            </p>
          ) : null}
          {notice ? (
            <p className="text-sm text-muted-foreground" role="status">
              {notice}
            </p>
          ) : null}

          <Button type="submit" className="w-full" disabled={pending}>
            {pending ? "Working…" : mode === "signin" ? "Sign in" : "Create account"}
          </Button>
        </form>

        <Button
          type="button"
          variant="link"
          className="mt-3 w-full"
          onClick={() => {
            setMode(mode === "signin" ? "signup" : "signin")
            setError(null)
            setNotice(null)
          }}
        >
          {mode === "signin"
            ? "Need an account? Sign up"
            : "Already have an account? Sign in"}
        </Button>
      </div>
    </main>
  )
}
