import { useTranslation } from "react-i18next";
import { GitFork } from "lucide-react";

interface ForkButtonProps {
  onClick: () => void;
}

export default function ForkButton({ onClick }: ForkButtonProps) {
  const { t } = useTranslation();

  return (
    <div className="flex justify-center mt-3">
      <button
        onClick={onClick}
        className="flex items-center gap-1.5 px-3 py-1.5 text-sm rounded-md
          text-gray-500 dark:text-gray-400
          hover:text-blue-600 dark:hover:text-blue-400
          hover:bg-blue-50 dark:hover:bg-blue-900/20
          border border-gray-300 dark:border-gray-600
          hover:border-blue-400 dark:hover:border-blue-500
          transition-colors cursor-pointer"
        title={t("common.forkTooltip")}
      >
        <GitFork className="w-3.5 h-3.5" />
        {t("common.fork")}
      </button>
    </div>
  );
}
