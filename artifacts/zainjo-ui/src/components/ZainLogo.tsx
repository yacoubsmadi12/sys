/**
 * Zain telecom logo — white version for dark backgrounds.
 * Matches the official Zain brand mark: circular emblem + wordmark.
 */
export default function ZainLogo({ className = "" }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 220 60"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
      aria-label="Zain"
      fill="none"
    >
      {/* Circle emblem */}
      <circle cx="30" cy="30" r="28" fill="white" opacity="0.95" />
      {/* Stylised Z swirl inside circle */}
      <path
        d="M18 20 Q30 14 38 22 Q28 30 22 30 Q32 30 42 38 Q34 46 22 40"
        stroke="#1a1a2e"
        strokeWidth="3.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />

      {/* Wordmark "zain" */}
      {/* z */}
      <path
        d="M68 22h14l-14 16h14"
        stroke="white"
        strokeWidth="3"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      {/* a */}
      <path
        d="M96 38 Q96 28 104 28 Q112 28 112 38 L112 38 M96 34 Q104 34 112 34"
        stroke="white"
        strokeWidth="3"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      {/* i — dot */}
      <circle cx="122" cy="24" r="2" fill="white" />
      {/* i — stem */}
      <line x1="122" y1="28" x2="122" y2="38" stroke="white" strokeWidth="3" strokeLinecap="round" />
      {/* n */}
      <path
        d="M132 38 L132 28 Q132 28 140 28 Q148 28 148 36 L148 38"
        stroke="white"
        strokeWidth="3"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}
