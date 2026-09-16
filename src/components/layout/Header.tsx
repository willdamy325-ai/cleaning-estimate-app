import Link from "next/link";

export function Header() {
  return (
    <header className="sticky top-0 z-30 border-b border-gold-soft/70 bg-mist/90 backdrop-blur-md">
      <div className="mx-auto flex max-w-content items-center justify-between px-5 py-3.5">
        <Link href="/" className="group flex items-center gap-3">
          <span className="flex h-10 w-10 items-center justify-center rounded-full border border-gold/50 bg-paper text-pine">
            <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" aria-hidden="true">
              <path
                d="M12 4c-3 4-6 6.5-6 10a6 6 0 0 0 12 0c0-3.5-3-6-6-10Z"
                stroke="currentColor"
                strokeWidth="1.5"
                strokeLinejoin="round"
              />
            </svg>
          </span>
          <span>
            <span className="block font-serif text-lg leading-none tracking-[0.18em] text-pine-deep">
              澄屋
            </span>
            <span className="mt-1 block text-[10px] tracking-[0.28em] text-clay">
              SUMIYA CLEANING
            </span>
          </span>
        </Link>
        <p className="hidden text-xs tracking-widest text-clay sm:block">見積依頼</p>
      </div>
    </header>
  );
}
