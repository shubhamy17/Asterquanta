import { useNavigate } from "react-router-dom";
import { Database, Activity, LayoutDashboard, Clock } from "lucide-react";

export const Layout = ({ children, activeJobCount }) => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen flex flex-col bg-slate-50">
      <header className="bg-white border-b border-slate-200 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 h-16 flex items-center justify-between">
          <div
            className="flex items-center gap-2 cursor-pointer group"
            onClick={() => navigate("/")}
          >
            <div className="bg-indigo-600 p-2 rounded-lg group-hover:bg-indigo-700 transition-colors">
              <Database className="w-5 h-5 text-white" />
            </div>
            <span className="text-xl font-bold text-slate-900 tracking-tight">
              Batch Processor
            </span>
          </div>

          <nav className="flex items-center gap-6">
            <div className="flex items-center gap-4 text-sm font-medium text-slate-600">
              <div className="flex items-center gap-1.5 hover:text-indigo-600 transition-colors cursor-pointer">
                <LayoutDashboard className="w-4 h-4" />
                <span>Dashboard</span>
              </div>
              <div className="flex items-center gap-1.5 hover:text-indigo-600 transition-colors cursor-pointer">
                <Clock className="w-4 h-4" />
                <span>History</span>
              </div>
            </div>

            <div className="h-6 w-px bg-slate-200 mx-2" />

            <div className="flex items-center gap-2 px-3 py-1.5 bg-indigo-50 rounded-full">
              <Activity
                className={`w-4 h-4 text-indigo-600 ${activeJobCount > 0 ? "animate-pulse" : ""}`}
              />
              <span className="text-sm font-semibold text-indigo-700">
                {activeJobCount} Active {activeJobCount === 1 ? "Job" : "Jobs"}
              </span>
            </div>
          </nav>
        </div>
      </header>

      <main className="flex-1">{children}</main>

      <footer className="bg-white border-t border-slate-200 py-6">
        <div className="max-w-7xl mx-auto px-4 text-center text-slate-500 text-sm">
          &copy; {new Date().getFullYear()} Batch Processor Systems. Built for
          high-performance transaction auditing.
        </div>
      </footer>
    </div>
  );
};
