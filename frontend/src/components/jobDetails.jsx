import React, { useState } from "react";
import {
  ArrowLeft,
  Filter,
  Search,
  ShieldAlert,
  CheckCircle,
  XCircle,
  Info,
} from "lucide-react";
import { TransactionList } from "./TransactionList";

export const JobDetails = ({ job, onBack }) => {
  const [filter, setFilter] = useState("all");
  const [search, setSearch] = useState("");

  const stats = [
    {
      label: "Total Records",
      value: job.total_records,
      icon: <Info className="w-4 h-4" />,
      color: "bg-slate-100 text-slate-700",
    },
    {
      label: "Valid",
      value: job.valid_records,
      icon: <CheckCircle className="w-4 h-4" />,
      color: "bg-emerald-100 text-emerald-700",
    },
    {
      label: "Suspicious",
      value: job.suspicious_records,
      icon: <ShieldAlert className="w-4 h-4" />,
      color: "bg-amber-100 text-amber-700",
    },
    {
      label: "Invalid",
      value: job.invalid_records,
      icon: <XCircle className="w-4 h-4" />,
      color: "bg-red-100 text-red-700",
    },
  ];

  const filteredTransactions = job.transactions.filter((t) => {
    const matchesFilter = filter === "all" || t.status === filter;
    const matchesSearch =
      t.transaction_id.toLowerCase().includes(search.toLowerCase()) ||
      t.user_id.toLowerCase().includes(search.toLowerCase());
    return matchesFilter && matchesSearch;
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
              {filteredTransactions.length} results
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

        <div className="flex-1 overflow-auto">
          <TransactionList transactions={filteredTransactions} />
        </div>
      </div>
    </div>
  );
};
