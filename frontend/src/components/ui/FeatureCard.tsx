import { Link } from "react-router-dom";
import type { LucideIcon } from "lucide-react";

interface FeatureCardProps {
  to: string;
  icon: LucideIcon;
  title: string;
  description: string;
}

export function FeatureCard({
  to,
  icon: Icon,
  title,
  description
}: FeatureCardProps) {
  return (
    <Link to={to} className="group h-full">
      <div className="bg-gray-50 dark:bg-gray-700 rounded-xl p-6 hover:shadow-lg transition-shadow h-full">
        <div className="w-12 h-12 bg-blue-100 dark:bg-blue-900 rounded-lg flex items-center justify-center mb-4 group-hover:bg-blue-600 transition-colors">
          <Icon
            className="w-6 h-6 text-blue-600 dark:text-blue-400 group-hover:text-white"
            strokeWidth={2}
          />
        </div>
        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-200 mb-2">
          {title}
        </h3>
        <p className="text-gray-600 dark:text-gray-400 text-sm">
          {description}
        </p>
      </div>
    </Link>
  );
}
