import { Link, useLocation } from "react-router-dom";

export default function Sidebar() {
  const location = useLocation();

  const navItems = [
    {
      path: "/outline-generator",
      label: "Course Outline Generator - Streaming",
      icon: "📝"
    },
    {
      path: "/structured-outline",
      label: "Course Outline Generator - Structured Output",
      icon: "⚡"
    },
    {
      path: "/lesson-planner",
      label: "Lesson Planner",
      icon: "📚"
    }
  ];

  return (
    <aside className="w-78 bg-white border-r border-gray-200 min-h-screen p-4">
      <nav className="space-y-2">
        {navItems.map((item) => {
          const isActive = location.pathname === item.path;
          return (
            <Link
              key={item.path}
              to={item.path}
              className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
                isActive
                  ? "bg-blue-50 text-blue-700 font-medium"
                  : "text-gray-700 hover:bg-gray-100"
              }`}
            >
              <span className="text-xl">{item.icon}</span>
              <span>{item.label}</span>
            </Link>
          );
        })}
      </nav>

      <hr className="my-6 border-gray-200" />

      <div className="space-y-4">
        {/* Additional sidebar content will go here */}
      </div>
    </aside>
  );
}
