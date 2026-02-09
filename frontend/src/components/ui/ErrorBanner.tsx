import { useTranslation } from "react-i18next";

interface ErrorBannerProps {
  /** The error string — can be an i18n key (e.g. "errors.invalidApiKey") or a raw message. */
  error: string | null;
  /** Called when the user dismisses the banner. */
  onDismiss: () => void;
}

/**
 * A dismissable red error banner.
 *
 * If `error` is `null` or empty the component renders nothing.
 * The error string is passed through `t()` so i18n keys are translated
 * automatically; raw strings fall back to themselves.
 */
export function ErrorBanner({ error, onDismiss }: ErrorBannerProps) {
  const { t } = useTranslation();

  if (!error) return null;

  return (
    <div className="mb-6 rounded-lg border border-red-200 dark:border-red-800 bg-red-50 dark:bg-red-950 p-4 flex items-start gap-3">
      {/* Warning icon */}
      <svg
        className="h-5 w-5 text-red-500 dark:text-red-400 mt-0.5 flex-shrink-0"
        fill="none"
        viewBox="0 0 24 24"
        strokeWidth={1.5}
        stroke="currentColor"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z"
        />
      </svg>

      {/* Content */}
      <div className="flex-1">
        <p className="text-sm font-medium text-red-800 dark:text-red-300">
          {t("errors.title")}
        </p>
        <p className="text-sm text-red-700 dark:text-red-400 mt-1">
          {t(error, error)}
        </p>
      </div>

      {/* Dismiss button */}
      <button
        onClick={onDismiss}
        className="text-red-400 hover:text-red-600 dark:hover:text-red-300 transition-colors"
        aria-label={t("common.dismiss", "Dismiss")}
      >
        <svg
          className="h-5 w-5"
          fill="none"
          viewBox="0 0 24 24"
          strokeWidth={1.5}
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M6 18 18 6M6 6l12 12"
          />
        </svg>
      </button>
    </div>
  );
}
