import { useState, useRef, useEffect } from "react";
import { useTranslation } from "react-i18next";
import { Cpu, ChevronDown } from "lucide-react";
import { useAuth } from "../../hooks/useAuth";
import { updateUserSettings } from "../../services/authService";

export default function ModelSelector() {
  const { t } = useTranslation();
  const { settings, refreshSettings } = useAuth();
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const models = settings?.available_models ?? [];
  const currentModel = models.find((m) => m.id === settings?.preferred_model);

  const handleModelChange = async (modelId: string) => {
    setIsOpen(false);
    if (modelId === settings?.preferred_model) return;
    try {
      await updateUserSettings({ preferred_model: modelId });
      await refreshSettings();
    } catch {
      /* silent fail — profile page is the place for error handling */
    }
  };

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(event.target as Node)
      ) {
        setIsOpen(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  return (
    <div className="mb-1">
      <div className="relative" ref={dropdownRef}>
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="w-full flex items-center gap-3 px-4 py-2 rounded-lg text-[#cddaef] hover:text-white hover:bg-[#333f51] focus:outline-none focus:border-transparent cursor-pointer transition-colors"
        >
          <Cpu className="w-5 h-5 opacity-70" />
          <div className="flex items-center justify-between flex-1 min-w-0">
            <span className="truncate">
              {currentModel?.label ?? t("sidebar.selectModel")}
            </span>
            <ChevronDown
              className={`w-4 h-4 shrink-0 transition-transform ${
                isOpen ? "rotate-180" : ""
              }`}
            />
          </div>
        </button>

        {isOpen && models.length > 0 && (
          <div className="absolute z-10 w-full mt-1 bg-[#2a3342] border border-[#3d4a5c] rounded-md shadow-lg">
            {models.map((model) => (
              <button
                key={model.id}
                onClick={() => handleModelChange(model.id)}
                className={`w-full flex flex-col px-3 py-2 text-sm text-left hover:bg-[#333f51] hover:text-white first:rounded-t-md last:rounded-b-md transition-colors ${
                  settings?.preferred_model === model.id
                    ? "bg-[#333f51] text-white font-medium"
                    : "text-[#cddaef]"
                }`}
              >
                <span>{model.label}</span>
                <span className="text-xs opacity-60">
                  {t(model.description_key)}
                </span>
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
