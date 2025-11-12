import { useState, useEffect, useRef } from "react";
import { useTranslation } from "react-i18next";

export function ScrollNavigationButtons() {
  const { t } = useTranslation();
  const [canScrollDown, setCanScrollDown] = useState(false);
  const [canScrollUp, setCanScrollUp] = useState(false);
  const [isScrollable, setIsScrollable] = useState(false);
  const scrollContainerRef = useRef<HTMLElement | null>(null);

  useEffect(() => {
    // Find the scrollable container (main element or document)
    const findScrollContainer = () => {
      // Check if we have a main element with overflow-y-auto
      const mainElement = document.querySelector(
        "main.overflow-y-auto"
      ) as HTMLElement;
      if (mainElement) {
        return mainElement;
      }

      // Otherwise check the document body with overflow-y-auto
      const bodyWithScroll = document.querySelector(
        "div.overflow-y-auto"
      ) as HTMLElement;
      if (bodyWithScroll) {
        return bodyWithScroll;
      }

      // Fallback to document element
      return document.documentElement;
    };

    scrollContainerRef.current = findScrollContainer();

    const checkScrollable = () => {
      const container = scrollContainerRef.current;
      if (!container) return;

      const scrollHeight = container.scrollHeight;
      const clientHeight = container.clientHeight;
      const scrollTop = container.scrollTop;

      const isScrollable = scrollHeight > clientHeight;
      const isNotAtBottom = scrollTop + clientHeight < scrollHeight - 100; // 100px threshold
      const isNotAtTop = scrollTop > 100; // 100px threshold

      setIsScrollable(isScrollable);
      setCanScrollDown(isScrollable && isNotAtBottom);
      setCanScrollUp(isScrollable && isNotAtTop);
    };

    // Check initially with a slight delay to ensure content is loaded
    setTimeout(checkScrollable, 100);

    // Check on scroll and resize
    const container = scrollContainerRef.current;
    if (container) {
      container.addEventListener("scroll", checkScrollable);
    }
    window.addEventListener("resize", checkScrollable);

    // Check on content changes (using MutationObserver)
    const observer = new MutationObserver(checkScrollable);
    observer.observe(document.body, {
      childList: true,
      subtree: true,
      attributes: true,
      characterData: true
    });

    return () => {
      if (container) {
        container.removeEventListener("scroll", checkScrollable);
      }
      window.removeEventListener("resize", checkScrollable);
      observer.disconnect();
    };
  }, []);

  const scrollToBottom = () => {
    const container = scrollContainerRef.current;
    if (container && canScrollDown) {
      container.scrollTo({
        top: container.scrollHeight,
        behavior: "smooth"
      });
    }
  };

  const scrollToTop = () => {
    const container = scrollContainerRef.current;
    if (container && canScrollUp) {
      container.scrollTo({
        top: 0,
        behavior: "smooth"
      });
    }
  };

  if (!isScrollable) {
    return null;
  }

  return (
    <div className="fixed top-1/2 -translate-y-1/2 right-4 z-40 flex flex-col gap-3">
      {/* Scroll to Top Button */}
      <button
        onClick={scrollToTop}
        disabled={!canScrollUp}
        className={`p-3 rounded-full shadow-lg transition-all flex items-center justify-center ${
          canScrollUp
            ? "bg-blue-600 text-white hover:bg-blue-700 hover:scale-110 cursor-pointer"
            : "bg-gray-300 text-gray-500 cursor-not-allowed opacity-40"
        }`}
        aria-label={t("common.scrollToTop")}
        title={t("common.scrollToTop")}
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
          strokeWidth={2.5}
          stroke="currentColor"
          className="w-6 h-6"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M4.5 10.5 12 3m0 0 7.5 7.5M12 3v18"
          />
        </svg>
      </button>

      {/* Scroll to Bottom Button */}
      <button
        onClick={scrollToBottom}
        disabled={!canScrollDown}
        className={`p-3 rounded-full shadow-lg transition-all flex items-center justify-center ${
          canScrollDown
            ? "bg-blue-600 text-white hover:bg-blue-700 hover:scale-110 cursor-pointer"
            : "bg-gray-300 text-gray-500 cursor-not-allowed opacity-40"
        }`}
        aria-label={t("common.scrollToBottom")}
        title={t("common.scrollToBottom")}
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
          strokeWidth={2.5}
          stroke="currentColor"
          className="w-6 h-6"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M19.5 13.5 12 21m0 0-7.5-7.5M12 21V3"
          />
        </svg>
      </button>
    </div>
  );
}
