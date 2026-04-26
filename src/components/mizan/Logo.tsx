export function MizanLogo({ className = "" }: { className?: string }) {
  return (
    <div className={`flex items-center gap-2.5 ${className}`}>
      <svg
        width="28"
        height="28"
        viewBox="0 0 32 32"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        aria-hidden="true"
      >
        {/* Center post */}
        <line x1="16" y1="6" x2="16" y2="26" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
        {/* Beam */}
        <line x1="5" y1="10" x2="27" y2="10" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
        {/* Left chains */}
        <line x1="6.5" y1="10.5" x2="6.5" y2="16" stroke="currentColor" strokeWidth="1" strokeLinecap="round" />
        {/* Right chains */}
        <line x1="25.5" y1="10.5" x2="25.5" y2="16" stroke="currentColor" strokeWidth="1" strokeLinecap="round" />
        {/* Pans */}
        <path d="M3 16 Q6.5 19 10 16" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" fill="none" />
        <path d="M22 16 Q25.5 19 29 16" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" fill="none" />
        {/* Base */}
        <line x1="12" y1="26" x2="20" y2="26" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
        {/* Top finial */}
        <circle cx="16" cy="5" r="1.2" fill="currentColor" />
      </svg>
      <span className="font-display text-xl font-medium tracking-tight">Mizan</span>
    </div>
  );
}
