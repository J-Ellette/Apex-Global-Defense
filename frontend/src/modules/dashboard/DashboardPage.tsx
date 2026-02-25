import { useAuthStore } from '../../app/providers/AuthProvider'
import { ClassificationBanner } from '../../shared/components/ClassificationBanner'

export default function DashboardPage() {
  const user = useAuthStore((s) => s.user)
  const classification = user?.classification ?? 'UNCLASS'

  return (
    <div className="min-h-screen flex flex-col bg-gray-950">
      <ClassificationBanner level={classification} />

      <main className="flex-1 px-6 py-8 max-w-7xl mx-auto w-full">
        <h1 className="text-2xl font-bold text-white mb-2">
          Welcome back, {user?.display_name ?? 'Analyst'}
        </h1>
        <p className="text-sm text-gray-400 mb-8">
          Clearance:{' '}
          <span className="font-semibold text-sky-400">{classification}</span>
          {' · '}
          {user?.roles.join(', ')}
        </p>

        {/* Module grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {MODULE_CARDS.map((card) => (
            <a
              key={card.href}
              href={card.href}
              className="group rounded-lg border border-gray-800 bg-gray-900 p-6 hover:border-sky-700 hover:bg-gray-800 transition-colors"
            >
              <div className="text-3xl mb-3">{card.icon}</div>
              <h2 className="text-base font-semibold text-white group-hover:text-sky-400 transition-colors">
                {card.title}
              </h2>
              <p className="mt-1 text-sm text-gray-400">{card.description}</p>
            </a>
          ))}
        </div>
      </main>

      <ClassificationBanner level={classification} />
    </div>
  )
}

const MODULE_CARDS = [
  {
    href: '/map',
    icon: '🗺️',
    title: 'Geospatial Map',
    description: 'Interactive 3D globe with military unit overlays, annotations, and layer control.',
  },
  {
    href: '/oob',
    icon: '🪖',
    title: 'Order of Battle',
    description: 'Explore and edit military force structures for 50+ nations.',
  },
  {
    href: '/simulation',
    icon: '⚔️',
    title: 'Simulation',
    description: 'Build conflict scenarios and run turn-based or real-time wargames.',
  },
  {
    href: '/intel',
    icon: '🔍',
    title: 'Intelligence',
    description: 'Ingest, search, and analyze OSINT/SIGINT/HUMINT items.',
  },
  {
    href: '/cyber',
    icon: '💻',
    title: 'Cyber Operations',
    description: 'MITRE ATT&CK catalog, infrastructure graph, and cyber attack simulation.',
  },
  {
    href: '/cbrn',
    icon: '☣️',
    title: 'CBRN Operations',
    description: 'Chemical, biological, radiological, and nuclear agent catalog, release planning, and Gaussian plume dispersion modeling.',
  },
  {
    href: '/asym',
    icon: '🕸️',
    title: 'Asymmetric / Insurgency',
    description: 'Insurgent cell network modeling, IED threat tracking, and COIN (counter-insurgency) planning.',
  },
  {
    href: '/terror',
    icon: '🚨',
    title: 'Terror Response',
    description: 'Site vulnerability assessment, terror threat scenario planning, and multi-agency response coordination.',
  },
  {
    href: '/civilian',
    icon: '👥',
    title: 'Civilian Impact',
    description: 'Population zone management, conflict civilian impact assessment, refugee flow modeling, and humanitarian corridor tracking.',
  },
  {
    href: '/reporting',
    icon: '📋',
    title: 'Reports',
    description: 'Auto-generate SITREP, INTSUM, and CONOPS briefs from simulation and intelligence data.',
  },
  {
    href: '/econ',
    icon: '💰',
    title: 'Economic Warfare',
    description: 'Sanction mapping, trade disruption modeling, and economic impact assessment.',
  },
  {
    href: '/infoops',
    icon: '📡',
    title: 'Information Operations',
    description: 'Track influence campaigns, disinformation indicators, and narrative threats.',
  },
  {
    href: '/admin',
    icon: '⚙️',
    title: 'Administration',
    description: 'Manage users, roles, AI providers, and system configuration.',
  },
]
