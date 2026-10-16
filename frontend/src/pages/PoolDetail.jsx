import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import api from "../api/client";

import { imgUrl } from "../api/client";

export default function PoolDetail() {
  const { id } = useParams();
  const { user, refreshUser } = useAuth();
  const [pool, setPool] = useState(null);
  const [loading, setLoading] = useState(true);
  const [drawing, setDrawing] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState("");

  const load = () => {
    api.getPool(id)
      .then(setPool)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, [id]);

  const handleDraw = async (type) => {
    if (!user) {
      setError("請先登入才能抽卡");
      return;
    }
    setDrawing(true);
    setError("");
    setResults(null);
    try {
      const res = await api.draw({ pool_id: Number(id), draw_type: type });
      setResults(res);
      await refreshUser();
      load();
    } catch (err) {
      setError(err.message);
    } finally {
      setDrawing(false);
    }
  };

  if (loading) return <div className="text-center py-20 text-pink-300">載入中...</div>;
  if (error && !pool) return <div className="text-center py-20 text-red-400">{error}</div>;
  if (!pool) return null;

  return (
    <div>
      <Link to="/" className="text-sm text-gray-400 hover:text-pink-300 mb-4 inline-block">← 返回獎池列表</Link>

      <div className="grid md:grid-cols-2 gap-8">
        <div>
          <div className="aspect-square rounded-2xl overflow-hidden bg-dark-800 border border-pink-900/30">
            {pool.image_url ? (
              <img src={imgUrl(pool.image_url)} alt={pool.name} className="w-full h-full object-cover" />
            ) : (
              <div className="w-full h-full flex items-center justify-center text-6xl text-gray-600">🎴</div>
            )}
          </div>
        </div>

        <div>
          <h1 className="text-2xl font-bold text-pink-300 mb-2">{pool.name}</h1>
          <p className="text-gray-400 mb-4 whitespace-pre-wrap">{pool.description || "暫無介紹"}</p>

          <div className="bg-dark-800/60 rounded-xl p-4 mb-6 border border-pink-900/20">
            <div className="flex justify-between text-sm mb-2">
              <span className="text-gray-400">剩餘 / 總數</span>
              <span className="text-yellow-300 font-semibold">
                {pool.remaining_quantity} / {pool.total_quantity}
              </span>
            </div>
            <div className="w-full bg-dark-900 rounded-full h-2">
              <div
                className="bg-gradient-to-r from-pink-500 to-purple-500 h-2 rounded-full transition-all"
                style={{ width: `${pool.total_quantity ? (pool.remaining_quantity / pool.total_quantity) * 100 : 0}%` }}
              />
            </div>
          </div>

          {error && <div className="bg-red-900/40 text-red-300 px-3 py-2 rounded text-sm mb-4">{error}</div>}

          <div className="flex gap-3">
            <button
              onClick={() => handleDraw("single")}
              disabled={drawing || pool.remaining_quantity < 1}
              className="flex-1 py-3 rounded-xl bg-pink-600 hover:bg-pink-500 disabled:opacity-40 font-medium transition"
            >
              {drawing ? "抽卡中..." : `單抽 ${pool.cost_single} pt`}
            </button>
            <button
              onClick={() => handleDraw("ten")}
              disabled={drawing || pool.remaining_quantity < 10}
              className="flex-1 py-3 rounded-xl bg-purple-600 hover:bg-purple-500 disabled:opacity-40 font-medium transition"
            >
              {drawing ? "抽卡中..." : `十連 ${pool.cost_ten} pt`}
            </button>
          </div>

          {!user && (
            <p className="text-center text-sm text-gray-500 mt-3">
              <Link to="/login" className="text-pink-400">登入</Link> 後即可開始抽卡
            </p>
          )}
        </div>
      </div>

      {results && (
        <div className="mt-10">
          <h2 className="text-xl font-semibold text-pink-300 mb-4">抽卡結果</h2>
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-4">
            {results.results.map((r, i) => (
              <div key={i} className="bg-dark-800 rounded-xl overflow-hidden border border-pink-500/30">
                <div className="aspect-square bg-dark-900">
                  {r.image_url ? (
                    <img src={imgUrl(r.image_url)} alt={r.name} className="w-full h-full object-cover" />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center text-3xl">🎴</div>
                  )}
                </div>
                <div className="p-2 text-center text-sm truncate">{r.name}</div>
              </div>
            ))}
          </div>
          <p className="text-center text-gray-400 mt-4">
            花費 {results.cost} pt · 剩餘 {results.remaining_points} pt
          </p>
        </div>
      )}

      {pool.cards && pool.cards.length > 0 && (
        <div className="mt-12">
          <h2 className="text-xl font-semibold mb-4 text-gray-300">獎池內容</h2>
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4">
            {pool.cards.map((c) => (
              <div key={c.id} className="bg-dark-800/40 rounded-xl overflow-hidden border border-gray-800">
                <div className="aspect-square bg-dark-900">
                  {c.image_url ? (
                    <img src={imgUrl(c.image_url)} alt={c.name} className="w-full h-full object-cover opacity-80" />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center text-2xl text-gray-600">🎴</div>
                  )}
                </div>
                <div className="p-2">
                  <div className="text-sm truncate">{c.name}</div>
                  <div className="text-xs text-gray-500">
                    剩 {c.remaining_quantity}/{c.total_quantity}
                    {c.original_probability != null && (
                      <span> · {(c.original_probability * 100).toFixed(1)}%</span>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
