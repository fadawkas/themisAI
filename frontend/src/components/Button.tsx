export default function Button({
  children,
  variant = "solid",
  onClick,
}: {
  children: React.ReactNode;
  variant?: "solid" | "outline";
  onClick?: () => void;
}) {
  const base = "px-4 py-2 rounded-2xl text-sm font-medium transition cursor-pointer";
  const solid =
    "bg-accent text-gray-900 hover:opacity-90 shadow-sm active:scale-[0.98]";
  const outline =
    "border border-accent text-gray-900 hover:bg-accent/30 active:scale-[0.98]";
  return (
    <button className={`${base} ${variant === "solid" ? solid : outline}`} onClick={onClick}>
      {children}
    </button>
  );
}
