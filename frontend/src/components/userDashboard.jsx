import React, { useState, useEffect, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { Layout } from "./layout";
import { UploadView } from "./uploadView";
import { JobDashboard } from "./jobDashboard";
import { JobDetails } from "./jobDetails";
import {
  ArrowLeft,
  User as UserIcon,
  Loader2,
  Wifi,
  WifiOff,
} from "lucide-react";
import { getUserById, getUserJobs } from "../services/api";
import { useJobWebSocket } from "../services/useJobWebSocket";

export const UserDashboard = () => {
  const { userId } = useParams();
  const navigate = useNavigate();
  const [activeJobId, setActiveJobId] = useState(null);
  const [jobs, setJobs] = useState([]);
  const [user, setUser] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  // Handle WebSocket progress updates
  const handleProgressUpdate = useCallback((data) => {
    if (data.type !== "job_progress") return;

    console.log("[WebSocket] Progress update for job:", data.job_id, data);

    setJobs((prevJobs) => {
      // Check if job exists in current state
      const jobExists = prevJobs.some((job) => job.id === data.job_id);

      if (jobExists) {
        // Update existing job
        return prevJobs.map((job) => {
          if (job.id === data.job_id) {
            console.log(
              "[WebSocket] Updating job:",
              job.id,
              "→",
              data.status,
              data.progress_percent + "%",
            );
            return {
              ...job,
              status: data.status,
              progress_percent: data.progress_percent,
              processed_records: data.processed_records,
              total_records: data.total_records,
              valid_records: data.valid_records,
              invalid_records: data.invalid_records,
              suspicious_records: data.suspicious_records,
            };
          }
          return job;
        });
      } else {
        // Job not in state yet - add it with the progress data
        console.log("[WebSocket] Adding new job from progress:", data.job_id);
        const newJob = {
          id: data.job_id,
          status: data.status,
          progress_percent: data.progress_percent,
          processed_records: data.processed_records,
          total_records: data.total_records,
          valid_records: data.valid_records,
          invalid_records: data.invalid_records,
          suspicious_records: data.suspicious_records,
          created_at: new Date().toISOString(),
        };
        return [newJob, ...prevJobs];
      }
    });
  }, []);

  // WebSocket connection for real-time updates
  const { isConnected } = useJobWebSocket(userId, handleProgressUpdate);

  useEffect(() => {
    if (!userId) return;

    const fetchData = async () => {
      try {
        const userData = await getUserById(userId);
        setUser(userData);
        const userJobs = await getUserJobs(userId);
        setJobs(userJobs);
      } catch (error) {
        console.error("Failed to fetch user data:", error);
        navigate("/");
        return;
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();

    // Fallback polling (longer interval since WebSocket handles real-time)
    // Only poll if WebSocket is disconnected or as a safety net
    const interval = setInterval(
      async () => {
        try {
          const userJobs = await getUserJobs(userId);
          const hasRunningJobs = userJobs.some((j) => j.status === "RUNNING");

          setJobs((prevJobs) => {
            if (JSON.stringify(prevJobs) !== JSON.stringify(userJobs)) {
              return userJobs;
            }
            return prevJobs;
          });

          // Stop polling if no jobs are running and WebSocket is connected
          if (!hasRunningJobs && isConnected) {
            clearInterval(interval);
          }
        } catch (error) {
          console.error("Failed to poll for job updates:", error);
        }
      },
      isConnected ? 30000 : 5000,
    ); // Poll less frequently when WebSocket connected

    return () => clearInterval(interval);
  }, [userId, navigate, isConnected]);

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
                #{user?.id}
              </span>
            </div>
            {/* WebSocket Status Indicator */}
            <div
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg border ${
                isConnected
                  ? "bg-emerald-50 border-emerald-200 text-emerald-700"
                  : "bg-amber-50 border-amber-200 text-amber-700"
              }`}
            >
              {isConnected ? (
                <Wifi className="w-3.5 h-3.5" />
              ) : (
                <WifiOff className="w-3.5 h-3.5" />
              )}
              <span className="text-xs font-medium">
                {isConnected ? "Live" : "Polling"}
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
