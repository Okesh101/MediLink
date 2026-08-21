import { useState } from "react";
import { MessageSquare, Clock, FileText } from "lucide-react";
import AIChat from "../../components/ai/AIChat";
import Timeline from "../../components/ai/Timeline";
import { Button } from "../../components/ui/Button";

export default function PatientAI() {
  const [activeTab, setActiveTab] = useState("chat");

  return (
    <div>
      <div className="mb-6">
        <h1 className="font-display text-2xl">AI Health Assistant</h1>
        <p className="text-muted">Chat with Meddy or view your health timeline</p>
      </div>

      <div className="flex gap-2 mb-6">
        <Button
          variant={activeTab === "chat" ? "default" : "outline"}
          onClick={() => setActiveTab("chat")}
          className="gap-2"
        >
          <MessageSquare className="h-4 w-4" />
          Chat
        </Button>
        <Button
          variant={activeTab === "timeline" ? "default" : "outline"}
          onClick={() => setActiveTab("timeline")}
          className="gap-2"
        >
          <Clock className="h-4 w-4" />
          Timeline
        </Button>
      </div>

      {activeTab === "chat" && <AIChat />}
      {activeTab === "timeline" && (
        <div className="bg-white rounded-2xl border border-line p-6">
          <Timeline />
        </div>
      )}
    </div>
  );
}
