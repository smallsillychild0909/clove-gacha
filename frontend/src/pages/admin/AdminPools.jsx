import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import api from "../../api/client";

import { imgUrl } from "../../api/client";

export default function AdminPools() {
  const [pools, setPools] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({
    name: "", description: "", intro_type: "image",
    cost_single: 100, cost_ten: 900, total_quantity: 100
  });
  const [image, setImage] = useState(null);
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState("");

  const load = () => api.listAllPools().then(setPools).catch(console.error);
  useEffect(() => { load(); }, []);

  const handleCreate = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMsg("");
    try {
      const fd = new FormData();
      Object.entries(form).forEach(([k, v]) => fd.append(k, v));
      if (image) fd.append("image", image);
      await api.adminCreatePool(fd);
      setMsg("獎池建立成功！");
      setShowForm(false);
      setForm({ name: "", description: "", intro_type: "image", cost_single: 100, cost_ten: 900, total_quantity: 100 });
      setImage(null);
      load();
    } catch (err) {
      setMsg("錯誤：" + err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-purple-300">獎池管理</h1>
        <button onClick={() => setShowForm(!showForm)}
          className="px-4 py-2 rounded-lg bg-purple-600 hover:bg-purple-500 transition">
          {showForm ? "取消" : "+ 新增獎池"}
        </button>
      </div>

      {msg && <div className="mb-4 text-sm text-green-300">{msg}</div>}

      {showForm && (
        <form onSubmit={handleCreate} className="bg-dark-800/60 rounded-2xl p-6 border border-purple-900/30 mb-8 space-y-4">
          <div className="grid sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm text-gray-400 mb-1">獎池名稱 *</label>
              <input required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })}
                className="w-full bg-dark-900 border border-gray-700 rounded-lg px-3 py-2" />
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-1">介紹類型</label>
              <select value={form.intro_type} onChange={(e) => setForm({ ...form, intro_type: e.target.value })}
                className="w-full bg-dark-900 border border-gray-700 rounded-lg px-3 py-2">
                <option value="image">圖片介紹</option>
                <option value="text">文字介紹</option>
              </select>
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-1">單抽費用 (pt)</label>
              <input type="number" min={1} value={form.cost_single} onChange={(e) => setForm({ ...form, cost_single: e.target.value })}
                className="w-full bg-dark-900 border border-gray-700 rounded-lg px-3 py-2" />
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-1">十連費用 (pt)</label>
              <input type="number" min={1} value={form.cost_ten} onChange={(e) => setForm({ ...form, cost_ten: e.target.value })}
                className="w-full bg-dark-900 border border-gray-700 rounded-lg px-3 py-2" />
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-1">獎池總數量 *（設定後才能新增卡面）</label>
              <input type="number" min={1} required value={form.total_quantity} onChange={(e) => setForm({ ...form, total_quantity: e.target.value })}
                className="w-full bg-dark-900 border border-gray-700 rounded-lg px-3 py-2" />
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-1">封面圖片</label>
              <input type="file" accept="image/*" onChange={(e) => setImage(e.target.files[0])}
                className="w-full text-sm text-gray-400" />
            </div>
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-1">介紹文字</label>
            <textarea value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })}
              rows={3} className="w-full bg-dark-900 border border-gray-700 rounded-lg px-3 py-2" />
          </div>
          <button type="submit" disabled={loading}
            className="px-6 py-2 rounded-lg bg-purple-600 hover:bg-purple-500 disabled:opacity-50">
            {loading ? "建立中..." : "建立獎池"}
          </button>
        </form>
      )}

      <div className="space-y-3">
        {pools.map((p) => (
          <div key={p.id} className="bg-dark-800/60 rounded-xl p-4 border border-purple-900/20 flex flex-wrap items-center gap-4">
            {p.image_url && (
              <img src={imgUrl(p.image_url)} alt="" className="w-16 h-16 object-cover rounded-lg" />
            )}
            <div className="flex-1 min-w-0">
              <div className="font-medium truncate">{p.name}</div>
              <div className="text-sm text-gray-400">
                剩餘 {p.remaining_quantity}/{p.total_quantity} · 單抽 {p.cost_single} · 十連 {p.cost_ten}
                {!p.is_active && <span className="text-red-400 ml-2">已關閉</span>}
              </div>
            </div>
            <Link to={`/admin/pools/${p.id}/cards`}
              className="px-3 py-1.5 rounded-lg bg-purple-900/50 hover:bg-purple-800 text-sm transition">
              管理卡面
            </Link>
          </div>
        ))}
        {pools.length === 0 && <p className="text-gray-500">尚無獎池，請先新增</p>}
      </div>
    </div>
  );
}
