import React, { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { Layout } from "./layout";
import { UploadView } from "./uploadView";
import { JobDashboard } from "./jobDashboard";
import { JobDetails } from "./JobDetails";
import { ArrowLeft, User as UserIcon, Loader2 } from "lucide-react";

export const UserDashboard = () => {
  const { userId } = useParams();
  const navigate = useNavigate();
  const [activeJobId, setActiveJobId] = useState(null);
  const [jobs, setJobs] = useState([]);
  const [user, setUser] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (!userId) return;

    const fetchData = async () => {
      //   const userData = await mockApiService.getUserById(userId);
      //   if (!userData) {
      //     navigate('/');
      //     return;
      //   }
      setUser({});
      //   const userJobs = await mockApiService.getAllJobs(userId);
      //   setJobs(userJobs);
      setIsLoading(false);
    };

    fetchData();

    // Polling simulation for live updates
    const interval = setInterval(async () => {
      //   const userJobs = await mockApiService.getAllJobs(userId);
      //   setJobs(prevJobs => {
      //     if (JSON.stringify(prevJobs) !== JSON.stringify(userJobs)) {
      //       return userJobs;
      //     }
      //     return prevJobs;
      //   });
    }, 2000);

    return () => clearInterval(interval);
  }, [userId, navigate]);

  const handleJobCreated = (job) => {
    setJobs((prev) => [job, ...prev]);
    setActiveJobId(job.id);
  };

  const handleJobSelect = (jobId) => {
    setActiveJobId(jobId);
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="w-10 h-10 text-indigo-600 animate-spin" />
          <p className="text-slate-500 font-medium">Loading workspace...</p>
        </div>
      </div>
    );
  }

  const activeJob = jobs.find((j) => j.id === activeJobId);

  return (
    <Layout activeJobCount={jobs.filter((j) => j.status === "running").length}>
      <div className="max-w-7xl mx-auto px-4 py-8 space-y-8">
        {/* User Header */}
        {!activeJobId && (
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
            <div className="flex items-center gap-4">
              <button
                onClick={() => navigate("/")}
                className="p-2 hover:bg-slate-100 rounded-lg transition-colors text-slate-500"
              >
                <ArrowLeft className="w-5 h-5" />
              </button>
              <div className="w-12 h-12 bg-indigo-100 rounded-xl flex items-center justify-center text-indigo-600">
                <UserIcon className="w-6 h-6" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-slate-900">
                  {user?.name}'s Workspace
                </h1>
                <p className="text-sm text-slate-500">{user?.email}</p>
              </div>
            </div>
            <div className="flex items-center gap-2 px-4 py-2 bg-slate-50 rounded-lg border border-slate-100">
              <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">
                Account ID:
              </span>
              <span className="text-xs font-mono text-slate-600">
                {/* {user?.id.substring(0, 8)}... */}
              </span>
            </div>
          </div>
        )}

        {!activeJobId ? (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            <div className="lg:col-span-1">
              <UploadView userId={userId} onJobCreated={handleJobCreated} />
            </div>
            <div className="lg:col-span-2">
              <JobDashboard jobs={jobs} onSelectJob={handleJobSelect} />
            </div>
          </div>
        ) : (
          <JobDetails job={activeJob} onBack={() => setActiveJobId(null)} />
        )}
      </div>
    </Layout>
  );
};
