import React, { useState, useEffect } from "react";
import {
  ArrowLeft,
  Filter,
  Search,
  ShieldAlert,
  CheckCircle,
  XCircle,
  Info,
  Loader2,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";
import { TransactionList } from "./TransactionList";
import { getJobStatus, getJobTransactions } from "../services/api";

export const JobDetails = ({ job: initialJob, onBack }) => {
  const [filter, setFilter] = useState("all");
  const [search, setSearch] = useState("");
  const [job, setJob] = useState(initialJob);
  const [transactions, setTransactions] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [totalCount, setTotalCount] = useState(0);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setIsLoading(true);
        // Fetch job status to get latest stats
        const jobStatus = await getJobStatus(job.id);
        setJob(jobStatus);

        // Fetch transactions with pagination
        const txns = await getJobTransactions(
          job.id,
          currentPage,
          pageSize,
          filter === "all" ? null : filter,
        );

        // Transform transactions to add status field
        const transformedTxns = txns.map((t) => ({
          ...t,
          status: !t.is_valid
            ? "invalid"
            : t.is_suspicious
              ? "suspicious"
              : "valid",
        }));

        setTransactions(transformedTxns);
        
        // Set total count based on filter
        if (filter === "all") {
          setTotalCount(jobStatus.total_records || 0);
        } else if (filter === "valid") {
          setTotalCount(jobStatus.valid_records || 0);
        } else if (filter === "suspicious") {
          setTotalCount(jobStatus.suspicious_records || 0);
        } else if (filter === "invalid") {
          setTotalCount(jobStatus.invalid_records || 0);
        }
      } catch (error) {
        console.error("Failed to fetch job details:", error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();

    // Only poll while job is RUNNING
    if (job.status !== "RUNNING") {
      return; // No polling needed for completed/failed jobs
    }

    // Poll for updates while job is running
    const interval = setInterval(async () => {
      try {
        const jobStatus = await getJobStatus(job.id);
        setJob(jobStatus);

        // If job completed, fetch final transactions and stop polling
        if (jobStatus.status !== "RUNNING") {
          const txns = await getJobTransactions(
            job.id,
            currentPage,
            pageSize,
            filter === "all" ? null : filter,
          );
          const transformedTxns = txns.map((t) => ({
            ...t,
            status: !t.is_valid
              ? "invalid"
              : t.is_suspicious
                ? "suspicious"
                : "valid",
          }));
          setTransactions(transformedTxns);
          clearInterval(interval);
        }
      } catch (error) {
        console.error("Failed to poll job status:", error);
      }
    }, 3000); // Poll every 3 seconds only while RUNNING

    return () => clearInterval(interval);
  }, [job.id, filter, currentPage, pageSize]);

  // Reset to page 1 when filter changes
  useEffect(() => {
    setCurrentPage(1);
  }, [filter]);

  // Pagination handlers
  const handlePageChange = (newPage) => {
    setCurrentPage(newPage);
  };

  const handlePageSizeChange = (newSize) => {
    setPageSize(Number(newSize));
    setCurrentPage(1); // Reset to first page when changing page size
  };

  const totalPages = Math.ceil(totalCount / pageSize);

  const stats = [
    {
      label: "Total Records",
      value: job.total_records || 0,
      icon: <Info className="w-4 h-4" />,
      color: "bg-slate-100 text-slate-700",
    },
    {
      label: "Valid",
      value: job.valid_records || 0,
      icon: <CheckCircle className="w-4 h-4" />,
      color: "bg-emerald-100 text-emerald-700",
    },
    {
      label: "Suspicious",
      value: job.suspicious_records || 0,
      icon: <ShieldAlert className="w-4 h-4" />,
      color: "bg-amber-100 text-amber-700",
    },
    {
      label: "Invalid",
      value: job.invalid_records || 0,
      icon: <XCircle className="w-4 h-4" />,
      color: "bg-red-100 text-red-700",
    },
  ];

  const filteredTransactions = transactions.filter((t) => {
    if (!search) return true;
    return (
      t.transaction_id?.toLowerCase().includes(search.toLowerCase()) ||
      t.user_id?.toLowerCase().includes(search.toLowerCase())
    );
  });

  return (
    <div className="space-y-6 animate-in fade-in slide-in-from-bottom-2 duration-300">
      <div className="flex items-center gap-4">
        <button
          onClick={onBack}
          className="p-2 hover:bg-white rounded-lg border border-transparent hover:border-slate-200 transition-all text-slate-500"
        >
          <ArrowLeft className="w-5 h-5" />
        </button>
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Job Details</h1>
          <p className="text-sm text-slate-500 font-mono">#{job.id}</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {stats.map((stat) => (
          <div
            key={stat.label}
            className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex items-center justify-between"
          >
            <div className="space-y-1">
              <p className="text-sm text-slate-500 font-medium">{stat.label}</p>
              <p className="text-2xl font-bold text-slate-900">
                {stat.value.toLocaleString()}
              </p>
            </div>
            <div className={`p-3 rounded-xl ${stat.color}`}>{stat.icon}</div>
          </div>
        ))}
      </div>

      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden min-h-[500px] flex flex-col">
        <div className="p-6 border-b border-slate-100 flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <h2 className="text-lg font-semibold text-slate-900">
              Transactions
            </h2>
            <div className="flex items-center gap-1 bg-indigo-50 px-2 py-1 rounded text-xs font-bold text-indigo-600">
              {totalCount > 0 
                ? `${(currentPage - 1) * pageSize + 1}-${Math.min(currentPage * pageSize, totalCount)} of ${totalCount}`
                : '0 results'}
            </div>
          </div>

          <div className="flex items-center gap-3">
            <div className="relative">
              <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
              <input
                type="text"
                placeholder="Search IDs..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-9 pr-4 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 w-full md:w-64"
              />
            </div>

            <div className="flex items-center gap-1 border border-slate-200 rounded-lg p-1 bg-slate-50">
              {["all", "valid", "suspicious", "invalid"].map((mode) => (
                <button
                  key={mode}
                  onClick={() => setFilter(mode)}
                  className={`px-3 py-1.5 text-xs font-semibold rounded-md transition-all capitalize
                    ${filter === mode ? "bg-white shadow-sm text-indigo-600" : "text-slate-500 hover:text-slate-700"}`}
                >
                  {mode}
                </button>
              ))}
            </div>
          </div>
        </div>

        <div className="flex-1 overflow-auto" style={{ maxHeight: '500px' }}>
          {isLoading ? (
            <div className="flex items-center justify-center py-20">
              <Loader2 className="w-8 h-8 text-indigo-600 animate-spin" />
            </div>
          ) : (
            <TransactionList transactions={filteredTransactions} />
          )}
        </div>

        {/* Pagination Controls */}
        {!isLoading && totalCount > 0 && (
          <div className="border-t border-slate-100 p-4 bg-slate-50 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="text-sm text-slate-600">Rows per page:</span>
              <select
                value={pageSize}
                onChange={(e) => handlePageSizeChange(e.target.value)}
                className="px-3 py-1.5 border border-slate-200 rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500"
              >
                <option value="10">10</option>
                <option value="20">20</option>
                <option value="50">50</option>
                <option value="100">100</option>
              </select>
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={() => handlePageChange(currentPage - 1)}
                disabled={currentPage === 1}
                className="p-2 rounded-lg hover:bg-white border border-slate-200 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>

              <div className="flex items-center gap-1">
                {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                  let pageNum;
                  if (totalPages <= 5) {
                    pageNum = i + 1;
                  } else if (currentPage <= 3) {
                    pageNum = i + 1;
                  } else if (currentPage >= totalPages - 2) {
                    pageNum = totalPages - 4 + i;
                  } else {
                    pageNum = currentPage - 2 + i;
                  }

                  return (
                    <button
                      key={pageNum}
                      onClick={() => handlePageChange(pageNum)}
                      className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-all
                        ${currentPage === pageNum 
                          ? 'bg-indigo-600 text-white' 
                          : 'hover:bg-white border border-slate-200 text-slate-700'}`}
                    >
                      {pageNum}
                    </button>
                  );
                })}
              </div>

              <button
                onClick={() => handlePageChange(currentPage + 1)}
                disabled={currentPage === totalPages}
                className="p-2 rounded-lg hover:bg-white border border-slate-200 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
