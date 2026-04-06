import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { Toaster } from "@/components/ui/toaster";
import { TooltipProvider } from "@/components/ui/tooltip";
import { ThemeProvider } from "@/components/ThemeProvider";
import Index from "./pages/Index";
import NotFound from "./pages/NotFound";
import DashboardLayout from "./components/dashboard/DashboardLayout";
import LeadDashboard from "./pages/LeadDashboard";
import CompanySetup from "./pages/CompanySetup";
import LeadSearch from "./pages/LeadSearch";
import LeadResults from "./pages/LeadResults";
import LeadDetail from "./pages/LeadDetail";
import LeadSettings from "./pages/LeadSettings";
import LoginPage from "./pages/Login";
import RegisterPage from "./pages/Register";

const queryClient = new QueryClient();

const App = () => (
  <ThemeProvider>
    <QueryClientProvider client={queryClient}>
      <TooltipProvider>
        <Toaster />
        <Sonner />
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<Index />} />
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
            <Route element={<DashboardLayout />}>
              <Route path="/dashboard" element={<LeadDashboard />} />
              <Route path="/company-setup" element={<CompanySetup />} />
              <Route path="/search" element={<LeadSearch />} />
              <Route path="/leads" element={<LeadResults />} />
              <Route path="/lead/:id" element={<LeadDetail />} />
              <Route path="/settings" element={<LeadSettings />} />
            </Route>
            <Route path="*" element={<NotFound />} />
          </Routes>
        </BrowserRouter>
      </TooltipProvider>
    </QueryClientProvider>
  </ThemeProvider>
);

export default App;
