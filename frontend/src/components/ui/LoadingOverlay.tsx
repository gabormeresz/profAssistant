import { useTranslation } from "react-i18next";
import { useEffect } from "react";

interface LoadingOverlayProps {
  message?: string;
  show: boolean;
}

export function LoadingOverlay({ message, show }: LoadingOverlayProps) {
  const { t } = useTranslation();

  // Parse and translate the message
  const getTranslatedMessage = (msg?: string): string => {
    if (!msg) return t("common.processing");

    // Try to parse as JSON (for messages with params)
    try {
      const parsed = JSON.parse(msg);
      if (parsed.key && parsed.params) {
        return t(parsed.key, parsed.params) as string;
      }
    } catch {
      // Not JSON, treat as a simple translation key
    }

    // Try to translate as a key, fallback to the message itself
    return t(msg, { defaultValue: msg }) as string;
  };

  const displayMessage = getTranslatedMessage(message);

  // Prevent navigation when overlay is shown
  useEffect(() => {
    if (!show) return;

    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      e.preventDefault();
      e.returnValue = "";
      return "";
    };

    window.addEventListener("beforeunload", handleBeforeUnload);

    return () => {
      window.removeEventListener("beforeunload", handleBeforeUnload);
    };
  }, [show]);

  if (!show) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center pointer-events-auto backdrop-blur-sm"
      style={{ backgroundColor: "rgba(0, 0, 0, 0.15)" }}
    >
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-2xl p-8 max-w-md mx-4 pointer-events-auto">
        <div className="flex flex-col items-center">
          {/* Spinner */}
          <div className="mb-6">
            <svg
              className="animate-spin h-16 w-16 text-blue-600 dark:text-blue-400"
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
            >
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
              />
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              />
            </svg>
          </div>

          {/* Message */}
          <h3 className="text-xl font-semibold text-dark mb-2 text-center">
            {displayMessage}
          </h3>

          {/* Warning */}
          <div className="mt-4 p-4 bg-yellow-50 dark:bg-yellow-950 border-l-4 border-yellow-400 rounded">
            <div className="flex">
              <div className="flex-shrink-0">
                <svg
                  className="h-5 w-5 text-yellow-400"
                  xmlns="http://www.w3.org/2000/svg"
                  viewBox="0 0 20 20"
                  fill="currentColor"
                >
                  <path
                    fillRule="evenodd"
                    d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
                    clipRule="evenodd"
                  />
                </svg>
              </div>
              <div className="ml-3">
                <p className="text-sm text-yellow-700 dark:text-yellow-300">
                  {t("overlay.doNotNavigate")}
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
