import { useEffect, useState, type FormEvent } from "react"
import { Navigate } from "react-router-dom"

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
      <div className="w-full max-w-sm rounded-lg border border-zinc-200 bg-white p-6 shadow-sm">
        <h1 className="text-xl font-medium text-zinc-900">Document Copilot</h1>
        <p className="mt-1 text-sm text-zinc-500">
          {mode === "signin"
            ? "Sign in with your email."
            : "Create an account with your email."}
        </p>

        <form className="mt-6 space-y-4" onSubmit={onSubmit}>
          <label className="block text-sm text-zinc-700">
            Email
            <input
              className="mt-1 w-full rounded-md border border-zinc-300 px-3 py-2 text-zinc-900"
              name="email"
              type="email"
              autoComplete="email"
              required
            />
          </label>
          <label className="block text-sm text-zinc-700">
            Password
            <input
              className="mt-1 w-full rounded-md border border-zinc-300 px-3 py-2 text-zinc-900"
              name="password"
              type="password"
              autoComplete={mode === "signin" ? "current-password" : "new-password"}
              minLength={6}
              required
            />
          </label>

          {error ? (
            <p className="text-sm text-red-700" role="alert">
              {error}
            </p>
          ) : null}
          {notice ? (
            <p className="text-sm text-zinc-700" role="status">
              {notice}
            </p>
          ) : null}

          <button
            className="w-full rounded-md bg-zinc-900 px-3 py-2 text-sm text-white disabled:opacity-60"
            type="submit"
            disabled={pending}
          >
            {pending ? "Working…" : mode === "signin" ? "Sign in" : "Create account"}
          </button>
        </form>

        <button
          className="mt-4 w-full text-sm text-zinc-600 underline"
          type="button"
          onClick={() => {
            setMode(mode === "signin" ? "signup" : "signin")
            setError(null)
            setNotice(null)
          }}
        >
          {mode === "signin"
            ? "Need an account? Sign up"
            : "Already have an account? Sign in"}
        </button>
      </div>
    </main>
  )
}
