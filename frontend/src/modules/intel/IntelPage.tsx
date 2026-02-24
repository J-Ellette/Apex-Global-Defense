import { useAuthStore } from '../../app/providers/AuthProvider'
import { ClassificationBanner } from '../../shared/components/ClassificationBanner'

export default function IntelPage() {
  const classification = useAuthStore((s) => s.user?.classification ?? 'UNCLASS')
  return (
    <div className="min-h-screen flex flex-col bg-gray-950">
      <ClassificationBanner level={classification} />
      <main className="flex-1 flex items-center justify-center">
        <p className="text-gray-400">Module under construction</p>
      </main>
      <ClassificationBanner level={classification} />
    </div>
  )
}
