import { useState } from "react";
import Sidebar from "../components/Sidebar";
import ChatBox from "../components/ChatBox";

function DashboardPage() {
  const [activeSession, setActiveSession] = useState(null);

  return (
    <div className="dashboard-layout">
      <Sidebar activeSession={activeSession} setActiveSession={setActiveSession} />
      <div className="flex-grow-1 d-flex flex-column" style={{ minWidth: 0 }}>
        <ChatBox activeSession={activeSession} onSessionCreated={setActiveSession} />
      </div>
    </div>
  );
}

export default DashboardPage;