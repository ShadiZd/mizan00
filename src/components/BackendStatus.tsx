import { useMizan } from "@/hooks/useMizan"

export function BackendStatus() {
  const { isBackendOnline } = useMizan()
  return (
    <div className="flex items-center gap-1.5">
      <div
        className={`w-2 h-2 rounded-full ${
          isBackendOnline ? "bg-green-400" : "bg-red-400"
        }`}
      />
      <span className="text-[10px] text-gray-400">
        {isBackendOnline ? "Live" : "Demo Mode"}
      </span>
    </div>
  )
}
