import { AlertTriangle, CheckCircle2, XCircle } from "lucide-react";
const TransactionStatus = {
  VALID: "valid",
  INVALID: "invalid",
  SUSPICIOUS: "suspicious",
};
export const TransactionList = ({ transactions }) => {
  const getStatusStyle = (status) => {
    switch (status) {
      case TransactionStatus.VALID:
        return {
          bg: "bg-emerald-50",
          text: "text-emerald-700",
          icon: <CheckCircle2 className="w-3.5 h-3.5" />,
        };
      case TransactionStatus.SUSPICIOUS:
        return {
          bg: "bg-amber-50",
          text: "text-amber-700",
          icon: <AlertTriangle className="w-3.5 h-3.5" />,
        };
      case TransactionStatus.INVALID:
        return {
          bg: "bg-red-50",
          text: "text-red-700",
          icon: <XCircle className="w-3.5 h-3.5" />,
        };
    }
  };

  return (
    <table className="w-full text-left border-collapse">
      <thead className="sticky top-0 bg-white shadow-sm z-10">
        <tr className="bg-slate-50/50 text-slate-500 text-[10px] font-bold uppercase tracking-widest border-b border-slate-100">
          <th className="px-6 py-3">Transaction ID</th>
          <th className="px-6 py-3">User ID</th>
          <th className="px-6 py-3">Amount</th>
          <th className="px-6 py-3">Timestamp</th>
          <th className="px-6 py-3">Status</th>
          <th className="px-6 py-3">Audit Logs</th>
        </tr>
      </thead>
      <tbody className="divide-y divide-slate-100">
        {transactions.length === 0 ? (
          <tr>
            <td
              colSpan={6}
              className="px-6 py-20 text-center text-slate-400 italic"
            >
              No matching transactions found.
            </td>
          </tr>
        ) : (
          transactions.map((t, idx) => {
            const style = getStatusStyle(t.status);
            return (
              <tr
                key={`${t.transaction_id}-${idx}`}
                className="hover:bg-slate-50/50 transition-colors"
              >
                <td className="px-6 py-4 font-mono text-[11px] text-slate-500">
                  {t.transaction_id}
                </td>
                <td className="px-6 py-4 font-mono text-[11px] text-slate-500">
                  {t.user_id}
                </td>
                <td className="px-6 py-4">
                  <span
                    className={`text-sm font-bold ${t.amount < 0 ? "text-red-600" : "text-slate-900"}`}
                  >
                    $
                    {t.amount.toLocaleString(undefined, {
                      minimumFractionDigits: 2,
                    })}
                  </span>
                </td>
                <td className="px-6 py-4 text-xs text-slate-500">
                  {new Date(t.timestamp).toLocaleString()}
                </td>
                <td className="px-6 py-4">
                  <div
                    className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold uppercase ${style.bg} ${style.text}`}
                  >
                    {style.icon}
                    {t.status}
                  </div>
                </td>
                <td className="px-6 py-4 max-w-xs">
                  <span className="text-xs text-slate-400 truncate block italic">
                    {t.error_message ||
                      (t.status === TransactionStatus.SUSPICIOUS
                        ? "Amount threshold flag"
                        : "Verified OK")}
                  </span>
                </td>
              </tr>
            );
          })
        )}
      </tbody>
    </table>
  );
};
