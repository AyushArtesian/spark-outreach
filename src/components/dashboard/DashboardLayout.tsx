import { useEffect, useState } from "react";
import { Outlet } from "react-router-dom";
import AppSidebar from "@/components/dashboard/AppSidebar";
import Topbar from "@/components/dashboard/Topbar";
import GlobalCommandBar from "@/components/dashboard/GlobalCommandBar";

export default function DashboardLayout() {
  const [commandOpen, setCommandOpen] = useState(false);

  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      const isMetaK = event.metaKey && event.key.toLowerCase() === "k";
      const isCtrlK = event.ctrlKey && event.key.toLowerCase() === "k";
      if (isMetaK || isCtrlK) {
        event.preventDefault();
        setCommandOpen((prev) => !prev);
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  return (
    <div className="flex min-h-screen w-full bg-background">
      <AppSidebar />
      <div className="flex-1 flex flex-col min-w-0">
        <Topbar onOpenCommandBar={() => setCommandOpen(true)} />
        <GlobalCommandBar open={commandOpen} onOpenChange={setCommandOpen} />
        <main className="flex-1 p-6 overflow-auto">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
