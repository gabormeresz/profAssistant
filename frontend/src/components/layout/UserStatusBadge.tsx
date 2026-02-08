import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { Settings, CheckCircle, AlertTriangle } from "lucide-react";
import { useAuth } from "../../hooks/useAuth";

export default function UserStatusBadge() {
  const { t } = useTranslation();
  const { settings } = useAuth();

  const hasApiKey = settings?.has_api_key ?? false;
  const modelLabel =
    settings?.available_models.find((m) => m.id === settings.preferred_model)
      ?.label ?? settings?.preferred_model;

  return (
    <Link
      to="/profile"
      className="rounded-lg px-4 py-2 flex items-center gap-3 text-[#cddaef] hover:text-white hover:bg-[#333f51] transition-colors"
      title={t("sidebar.profileSettings")}
    >
      <Settings className="w-5 h-5 shrink-0" />

      <span className="flex items-center gap-1.5 shrink-0">
        <span>{t("sidebar.apiKey")}</span>
        {hasApiKey ? (
          <CheckCircle className="w-4 h-4 text-emerald-400" />
        ) : (
          <AlertTriangle className="w-4 h-4 text-amber-400" />
        )}
      </span>

      {modelLabel && (
        <>
          <span className="text-[#3d4a5c]">|</span>
          <span className="truncate">{modelLabel}</span>
        </>
      )}
    </Link>
  );
}
