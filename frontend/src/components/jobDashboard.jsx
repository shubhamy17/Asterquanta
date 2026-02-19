import {
  PlayCircle,
  CheckCircle,
  Clock,
  AlertCircle,
  ChevronRight,
  BarChart3,
} from "lucide-react";

export const JobDashboard = ({ jobs, onSelectJob }) => {
  const getStatusIcon = (status) => {
    switch (status) {
      case "RUNNING":
        return <Clock className="w-4 h-4 text-blue-500 animate-spin" />;
      case "COMPLETED":
        return <CheckCircle className="w-4 h-4 text-emerald-500" />;
      case "FAILED":
        return <AlertCircle className="w-4 h-4 text-red-500" />;
      default:
        return <PlayCircle className="w-4 h-4 text-slate-400" />;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case "RUNNING":
        return "bg-blue-50 text-blue-700 border-blue-100";
      case "COMPLETED":
        return "bg-emerald-50 text-emerald-700 border-emerald-100";
      case "FAILED":
        return "bg-red-50 text-red-700 border-red-100";
      default:
        return "bg-slate-50 text-slate-700 border-slate-100";
    }
  };

  return (
    <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
      <div className="p-6 border-b border-slate-100 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <BarChart3 className="w-5 h-5 text-slate-400" />
          <h2 className="text-lg font-semibold text-slate-900">Job History</h2>
        </div>
        <span className="px-2 py-0.5 bg-slate-100 text-slate-500 text-xs font-bold rounded uppercase">
          {jobs.length} Total
        </span>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="bg-slate-50/50 text-slate-500 text-xs font-semibold uppercase tracking-wider">
              <th className="px-6 py-4">Job ID</th>
              <th className="px-6 py-4">Status</th>
              <th className="px-6 py-4">Progress</th>
              <th className="px-6 py-4">Stats</th>
              <th className="px-6 py-4">Created</th>
              <th className="px-6 py-4 text-right">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {jobs.length === 0 ? (
              <tr>
                <td
                  colSpan={6}
                  className="px-6 py-12 text-center text-slate-400 italic"
                >
                  No jobs processed yet. Upload a CSV to get started.
                </td>
              </tr>
            ) : (
              jobs.map((job) => (
                <tr
                  key={job.id}
                  className="hover:bg-slate-50 transition-colors group"
                >
                  <td className="px-6 py-4">
                    <span className="font-mono text-xs text-slate-500">
                      #{job.id}
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    <div
                      className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border ${getStatusColor(job.status)}`}
                    >
                      {getStatusIcon(job.status)}
                      <span className="capitalize">{job.status}</span>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <div className="w-32 space-y-1.5">
                      <div className="flex items-center justify-between text-[10px] font-bold text-slate-400">
                        <span>{job.progress_percent}%</span>
                        <span>{job.total_records} Recs</span>
                      </div>
                      <div className="h-1.5 w-full bg-slate-100 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-indigo-500 transition-all duration-500"
                          style={{ width: `${job.progress_percent}%` }}
                        />
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex gap-2">
                      <div className="flex flex-col">
                        <span className="text-xs text-slate-400">Valid</span>
                        <span className="text-xs font-bold text-emerald-600">
                          {job.valid_records}
                        </span>
                      </div>
                      <div className="flex flex-col">
                        <span className="text-xs text-slate-400">
                          Suspicious
                        </span>
                        <span className="text-xs font-bold text-amber-500">
                          {job.suspicious_records}
                        </span>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <span className="text-xs text-slate-500">
                      {new Date(job.created_at).toLocaleTimeString([], {
                        hour: "2-digit",
                        minute: "2-digit",
                      })}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-right">
                    <button
                      onClick={() => onSelectJob(job.id)}
                      className="inline-flex items-center gap-1 text-xs font-bold text-indigo-600 hover:text-indigo-700 transition-colors"
                    >
                      View Details
                      <ChevronRight className="w-3 h-3 transition-transform group-hover:translate-x-0.5" />
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};
