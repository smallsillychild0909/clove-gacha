import { useEffect, useState } from "react";
import api from "../api/client";

import { imgUrl } from "../api/client";

export default function MyRecords() {
  const [draws, setDraws] = useState([]);
  const [txs, setTxs] = useState([]);
  const [tab, setTab] = useState("draw");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([api.myDrawRecords(), api.myTransactions()])
      .then(([d, t]) => { setDraws(d); setTxs(t); })
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="text-center py-20 text-pink-300">載入中...</div>;

  return (
    <div>
      <h1 className="text-2xl font-bold text-pink-300 mb-6">我的紀錄</h1>
      <div className="flex gap-2 mb-6">
        <button onClick={() => setTab("draw")} className={`px-4 py-2 rounded-lg ${tab === "draw" ? "bg-pink-600" : "bg-dark-800"}`}>
          抽卡紀錄
        </button>
        <button onClick={() => setTab("tx")} className={`px-4 py-2 rounded-lg ${tab === "tx" ? "bg-pink-600" : "bg-dark-800"}`}>
          消費紀錄
        </button>
      </div>

      {tab === "draw" && (
        <div className="space-y-4">
          {draws.length === 0 && <p className="text-gray-500">尚無抽卡紀錄</p>}
          {draws.map((r) => (
            <div key={r.id} className="bg-dark-800/60 rounded-xl p-4 border border-pink-900/20">
              <div className="flex justify-between text-sm text-gray-400 mb-2">
                <span>{r.pool_name || `獎池 #${r.pool_id}`}</span>
                <span>{r.created_at} · {r.draw_type === "single" ? "單抽" : "十連"} · -{r.cost_points} pt</span>
              </div>
              <div className="flex flex-wrap gap-2">
                {(r.results || []).map((c, i) => (
                  <div key={i} className="flex items-center gap-2 bg-dark-900 rounded-lg px-2 py-1 text-sm">
                    {c.image_url && <img src={imgUrl(c.image_url)} alt="" className="w-8 h-8 object-cover rounded" />}
                    <span>{c.name}</span>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      {tab === "tx" && (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-gray-400 border-b border-gray-800">
                <th className="py-2 pr-4">時間</th>
                <th className="py-2 pr-4">類型</th>
                <th className="py-2 pr-4">金額</th>
                <th className="py-2 pr-4">餘額</th>
                <th className="py-2">備註</th>
              </tr>
            </thead>
            <tbody>
              {txs.map((t) => (
                <tr key={t.id} className="border-b border-gray-900">
                  <td className="py-2 pr-4 text-gray-500">{t.created_at}</td>
                  <td className="py-2 pr-4">{t.type}</td>
                  <td className={`py-2 pr-4 font-medium ${t.amount > 0 ? "text-green-400" : "text-red-400"}`}>
                    {t.amount > 0 ? "+" : ""}{t.amount}
                  </td>
                  <td className="py-2 pr-4">{t.balance_after}</td>
                  <td className="py-2 text-gray-400">{t.note}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {txs.length === 0 && <p className="text-gray-500 mt-4">尚無消費紀錄</p>}
        </div>
      )}
    </div>
  );
}
