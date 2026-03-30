export function getWsUrl(simId: string): string {
  const wsBase =
    typeof window !== "undefined" && process.env.NEXT_PUBLIC_WS_URL
      ? process.env.NEXT_PUBLIC_WS_URL
      : "ws://localhost:8000";
  return `${wsBase}/ws/simulations/${simId}`;
}
