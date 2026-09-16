export function Footer() {
  return (
    <footer className="border-t border-gold-soft/80 bg-pine-deep text-gold-pale">
      <div className="mx-auto flex max-w-content flex-col gap-2 px-5 py-8 text-center sm:flex-row sm:items-center sm:justify-between sm:text-left">
        <p className="font-serif tracking-[0.2em]">澄屋 SUMIYA</p>
        <p className="text-xs text-gold-soft">
          本見積は概算です。現地状況により金額が変わる場合があります。
        </p>
      </div>
    </footer>
  );
}
