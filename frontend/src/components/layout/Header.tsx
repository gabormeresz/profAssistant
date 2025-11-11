import { useState, useEffect, useRef } from "react";

export default function Header({ title }: { title?: string }) {
  const [isScrolled, setIsScrolled] = useState(false);
  const headerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleScroll = () => {
      if (headerRef.current) {
        const scrollContainer = headerRef.current.closest("main") || window;
        const scrollTop =
          scrollContainer === window
            ? window.scrollY
            : (scrollContainer as HTMLElement).scrollTop;
        setIsScrolled(scrollTop > 0);
      }
    };

    const scrollContainer = headerRef.current?.closest("main") || window;
    scrollContainer.addEventListener("scroll", handleScroll);

    return () => {
      scrollContainer.removeEventListener("scroll", handleScroll);
    };
  }, []);

  return (
    <div
      ref={headerRef}
      className={`sticky top-0 z-10 pt-6 pb-4 text-center transition-shadow duration-200 ${
        isScrolled ? "shadow-md border-b border-gray-200" : ""
      }`}
      style={{ backgroundColor: "#f3f4f4" }}
    >
      <h1 className="text-3xl font-bold text-dark mb-2">{title}</h1>
    </div>
  );
}
