import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import api from "../../api/client";

import { imgUrl } from "../../api/client";

export default function AdminPoolCards() {
  const { id } = useParams();
  const [data, setData] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ name: "", total_quantity: 10, original_probability: "" });
  const [image, setImage] = useState(null);
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState("");

  const load = () => api.adminListCards(id).then(setData).catch(console.error);
  useEffect(() => { load(); }, [id]);

  const handleAdd = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMsg("");
    try {
      const fd = new FormData();
      fd.append("name", form.name);
      fd.append("total_quantity", form.total_quantity);
      if (form.original_probability !== "") fd.append("original_probability", form.original_probability);
      if (image) fd.append("image", image);
      await api.adminAddCard(id, fd);
      setMsg("卡面新增成功！");
      setShowForm(false);
      setForm({ name: "", total_quantity: 10, original_probability: "" });
      setImage(null);
      load();
    } catch (err) {
      setMsg("錯誤：" + err.message);
    } finally {
      setLoading(false);
    }
  };

  if (!data) return <div className="text-center py-20 text-purple-300">載入中...</div>;
  const { pool, cards } = data;
  const sumQty = cards.reduce((s, c) => s + c.total_quantity, 0);

  return (
    <div>
      <Link to="/admin/pools" className="text-sm text-gray-400 hover:text-purple-300 mb-4 inline-block">← 返回獎池列表</Link>
      <h1 className="text-2xl font-bold text-purple-300 mb-1">{pool.name} - 卡面管理</h1>
      <p className="text-gray-400 mb-6">
        獎池總量 {pool.total_quantity} · 已設定卡面總數 {sumQty} · 剩餘可分配 {pool.total_quantity - sumQty}
      </p>

      {msg && <div className="mb-4 text-sm text-green-300">{msg}</div>}

      <div className="mb-6">
        <button onClick={() => setShowForm(!showForm)}
          className="px-4 py-2 rounded-lg bg-purple-600 hover:bg-purple-500 transition"
          disabled={sumQty >= pool.total_quantity}>
          {showForm ? "取消" : "+ 新增卡面"}
        </button>
      </div>

      {showForm && (
        <form onSubmit={handleAdd} className="bg-dark-800/60 rounded-2xl p-6 border border-purple-900/30 mb-8 space-y-4">
          <div className="grid sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm text-gray-400 mb-1">卡面名稱 *</label>
              <input required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })}
                className="w-full bg-dark-900 border border-gray-700 rounded-lg px-3 py-2" />
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-1">可抽出張數 *</label>
              <input type="number" min={1} required value={form.total_quantity}
                onChange={(e) => setForm({ ...form, total_quantity: e.target.value })}
                className="w-full bg-dark-900 border border-gray-700 rounded-lg px-3 py-2" />
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-1">原始概率（0~1，可留空自動計算）</label>
              <input type="number" step="0.001" min={0} max={1} value={form.original_probability}
                onChange={(e) => setForm({ ...form, original_probability: e.target.value })}
                className="w-full bg-dark-900 border border-gray-700 rounded-lg px-3 py-2" placeholder="例如 0.05" />
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-1">卡面圖片</label>
              <input type="file" accept="image/*" onChange={(e) => setImage(e.target.files[0])}
                className="w-full text-sm text-gray-400" />
            </div>
          </div>
          <button type="submit" disabled={loading}
            className="px-6 py-2 rounded-lg bg-purple-600 hover:bg-purple-500 disabled:opacity-50">
            {loading ? "新增中..." : "新增卡面"}
          </button>
        </form>
      )}

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-gray-400 border-b border-gray-800">
              <th className="py-2 pr-4">圖片</th>
              <th className="py-2 pr-4">卡片名稱</th>
              <th className="py-2 pr-4">總數</th>
              <th className="py-2 pr-4">已抽出</th>
              <th className="py-2 pr-4">剩餘</th>
              <th className="py-2">原始概率</th>
            </tr>
          </thead>
          <tbody>
            {cards.map((c) => (
              <tr key={c.id} className="border-b border-gray-900">
                <td className="py-2 pr-4">
                  {c.image_url ? (
                    <img src={imgUrl(c.image_url)} alt="" className="w-12 h-12 object-cover rounded" />
                  ) : "—"}
                </td>
                <td className="py-2 pr-4 font-medium">{c.name}</td>
                <td className="py-2 pr-4">{c.total_quantity}</td>
                <td className="py-2 pr-4">{c.total_quantity - c.remaining_quantity}</td>
                <td className="py-2 pr-4 text-yellow-300">{c.remaining_quantity}</td>
                <td className="py-2">{(c.original_probability * 100).toFixed(2)}%</td>
              </tr>
            ))}
          </tbody>
        </table>
        {cards.length === 0 && <p className="text-gray-500 mt-4">尚未新增任何卡面</p>}
      </div>
    </div>
  );
}
