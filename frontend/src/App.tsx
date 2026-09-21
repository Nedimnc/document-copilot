import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom"

import { AuthGate } from "@/components/AuthGate"
import { Toaster } from "@/components/ui/sonner"
import { TooltipProvider } from "@/components/ui/tooltip"
import { ChatLayout } from "@/pages/chat/ChatLayout"
import { ChatPage } from "@/pages/chat/ChatPage"
import { ThreadListPage } from "@/pages/chat/ThreadListPage"
import { LoginPage } from "@/pages/LoginPage"

export default function App() {
  return (
    <TooltipProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route
            element={
              <AuthGate>
                <ChatLayout />
              </AuthGate>
            }
          >
            <Route path="/" element={<ThreadListPage />} />
            <Route path="/chats/:threadId" element={<ChatPage />} />
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
      <Toaster />
    </TooltipProvider>
  )
}
