import React, { useState, useRef } from "react";
import {
  Upload,
  FileText,
  X,
  CheckCircle2,
  AlertCircle,
  Loader2,
} from "lucide-react";
import { uploadFile, startJob } from "../services/api";

export const UploadView = ({ userId, onJobCreated }) => {
  const [file, setFile] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState(null);
  const fileInputRef = useRef(null);

  const handleFileChange = (e) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      if (
        selectedFile.type !== "text/csv" &&
        !selectedFile.name.endsWith(".csv")
      ) {
        setError("Please upload a valid CSV file");
        return;
      }
      setError(null);
      setFile(selectedFile);
    }
  };

  const handleUpload = async () => {
    if (!file) return;

    setIsUploading(true);
    setError(null);

    try {
      const response = await uploadFile(userId, file);
      const jobId = response.job_id;

      // Automatically start the job
      await startJob(jobId);

      // Notify parent component
      onJobCreated({ id: jobId, status: "RUNNING" });
      setFile(null);
    } catch (err) {
      setError(err.response?.data?.detail || err?.message || "Upload failed");
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 space-y-6">
      <div className="space-y-1">
        <h2 className="text-lg font-semibold text-slate-900">
          Upload Transactions
        </h2>
        <p className="text-sm text-slate-500">
          Process CSV files with bulk transaction data.
        </p>
      </div>

      <div
        onClick={() => fileInputRef.current?.click()}
        className={`relative border-2 border-dashed rounded-xl p-8 transition-all cursor-pointer flex flex-col items-center justify-center gap-3
          ${file ? "border-indigo-500 bg-indigo-50" : "border-slate-200 hover:border-indigo-400 hover:bg-slate-50"}`}
      >
        <input
          type="file"
          ref={fileInputRef}
          onChange={handleFileChange}
          className="hidden"
          accept=".csv"
        />

        {file ? (
          <div className="flex flex-col items-center text-center">
            <div className="bg-indigo-600 p-2 rounded-lg mb-3 shadow-lg shadow-indigo-200">
              <FileText className="w-6 h-6 text-white" />
            </div>
            <p className="text-sm font-medium text-slate-900 truncate max-w-[200px]">
              {file.name}
            </p>
            <p className="text-xs text-slate-500 mt-1">
              {(file.size / 1024).toFixed(1)} KB
            </p>
            <button
              onClick={(e) => {
                e.stopPropagation();
                setFile(null);
              }}
              className="mt-4 p-1.5 hover:bg-white rounded-full transition-colors text-slate-400 hover:text-red-500"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        ) : (
          <>
            <div className="bg-slate-100 p-3 rounded-full">
              <Upload className="w-6 h-6 text-slate-400" />
            </div>
            <div className="text-center">
              <p className="text-sm font-medium text-slate-900">
                Click to browse or drag & drop
              </p>
              <p className="text-xs text-slate-400 mt-1">
                transaction_id, user_id, amount, timestamp
              </p>
            </div>
          </>
        )}
      </div>

      {error && (
        <div className="flex items-center gap-2 p-3 bg-red-50 text-red-700 text-sm rounded-lg border border-red-100">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <p>{error}</p>
        </div>
      )}

      <button
        disabled={!file || isUploading}
        onClick={handleUpload}
        className="w-full bg-indigo-600 text-white py-2.5 rounded-lg font-medium shadow-md shadow-indigo-100 hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center justify-center gap-2"
      >
        {isUploading ? (
          <>
            <Loader2 className="w-4 h-4 animate-spin" />
            Processing...
          </>
        ) : (
          <>
            <CheckCircle2 className="w-4 h-4" />
            Start New Job
          </>
        )}
      </button>

      <div className="pt-4 border-t border-slate-100">
        <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">
          Validation Requirements
        </h3>
        <ul className="space-y-2 text-xs text-slate-500">
          <li className="flex items-start gap-2">
            <div className="w-1 h-1 rounded-full bg-slate-300 mt-1.5" />
            <span>IDs must be valid GUID/UUID format</span>
          </li>
          <li className="flex items-start gap-2">
            <div className="w-1 h-1 rounded-full bg-slate-300 mt-1.5" />
            <span>Amount must be numeric</span>
          </li>
          <li className="flex items-start gap-2">
            <div className="w-1 h-1 rounded-full bg-slate-300 mt-1.5" />
            <span>Timestamp must be ISO 8601</span>
          </li>
        </ul>
      </div>
    </div>
  );
};
