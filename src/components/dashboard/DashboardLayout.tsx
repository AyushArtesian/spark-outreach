import { Outlet } from "react-router-dom";
import AppSidebar from "@/components/dashboard/AppSidebar";
import Topbar from "@/components/dashboard/Topbar";

export default function DashboardLayout() {
  return (
    <div className="flex min-h-screen w-full bg-background">
      <AppSidebar />
      <div className="flex-1 flex flex-col min-w-0">
        <Topbar />
        <main className="flex-1 p-6 overflow-auto">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
