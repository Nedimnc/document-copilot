export function ThreadListPage() {
  return (
    <main className="flex flex-1 items-center justify-center px-6 text-center">
      <div>
        <h1 className="text-xl font-medium text-zinc-900">Conversations</h1>
        <p className="mt-2 max-w-sm text-sm text-zinc-500">
          Create a thread from the sidebar, send a message, and you should see a
          stubbed streamed reply. Reload the thread to confirm history was saved.
        </p>
      </div>
    </main>
  )
}
