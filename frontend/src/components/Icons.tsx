export function HandTick({ size = 20 }: { size?: number }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      className="hand-icon"
      aria-hidden="true"
    >
      <path
        d="M4.5 12.5L9.5 17.5L19.5 6.5"
        stroke="var(--correct-green)"
        strokeWidth="2.5"
      />
    </svg>
  );
}

export function HandCross({ size = 20 }: { size?: number }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      className="hand-icon"
      aria-hidden="true"
    >
      <path
        d="M6 6L18 18M6 18L18 6"
        stroke="var(--examiner-red)"
        strokeWidth="2.5"
      />
    </svg>
  );
}

export function HandCircle({ size = 64, color = 'var(--examiner-red)' }: { size?: number; color?: string }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 100 100"
      className="hand-icon"
      aria-hidden="true"
    >
      <path
        d="M 50 10 C 25 10, 10 25, 10 50 C 10 75, 25 90, 50 90 C 78 90, 90 73, 90 48 C 90 22, 72 8, 46 12"
        stroke={color}
        strokeWidth="4"
      />
    </svg>
  );
}
