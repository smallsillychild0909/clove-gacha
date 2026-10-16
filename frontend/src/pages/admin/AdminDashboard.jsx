import { Link } from "react-router-dom";

export default function AdminDashboard() {
  const cards = [
    { to: "/admin/pools", title: "獎池管理", desc: "新增 / 編輯活動卡池", icon: "🎴" },
    { to: "/admin/recharge", title: "儲值管理", desc: "手動儲值 & 系統測試儲值", icon: "💰" },
    { to: "/admin/records", title: "消費與抽卡紀錄", desc: "查看所有會員紀錄", icon: "📋" },
  ];

  return (
    <div>
      <h1 className="text-2xl font-bold text-purple-300 mb-6">管理控台</h1>
      <div className="grid sm:grid-cols-3 gap-6">
        {cards.map((c) => (
          <Link key={c.to} to={c.to}
            className="bg-dark-800/60 rounded-2xl p-6 border border-purple-900/30 hover:border-purple-500/50 transition group">
            <div className="text-4xl mb-3">{c.icon}</div>
            <h2 className="text-lg font-semibold group-hover:text-purple-300 transition">{c.title}</h2>
            <p className="text-sm text-gray-400 mt-1">{c.desc}</p>
          </Link>
        ))}
      </div>
    </div>
  );
}
