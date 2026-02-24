import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useAuthStore } from '../../app/providers/AuthProvider'
import { ClassificationBanner } from '../../shared/components/ClassificationBanner'
import { LoadingSpinner } from '../../shared/components/LoadingSpinner'
import { oobApi } from '../../shared/api/endpoints'
import type { Country, MilitaryUnit } from '../../shared/api/types'

export default function OobPage() {
  const classification = useAuthStore((s) => s.user?.classification ?? 'UNCLASS')
  const [selectedCountry, setSelectedCountry] = useState<Country | null>(null)

  const { data: countries, isLoading: loadingCountries, error: countriesError } = useQuery({
    queryKey: ['oob', 'countries'],
    queryFn: () => oobApi.listCountries(),
    staleTime: 5 * 60 * 1000,
  })

  const { data: forces, isLoading: loadingForces } = useQuery({
    queryKey: ['oob', 'forces', selectedCountry?.code],
    queryFn: () => oobApi.listForces(selectedCountry!.code),
    enabled: !!selectedCountry,
    staleTime: 5 * 60 * 1000,
  })

  return (
    <div className="min-h-screen flex flex-col bg-gray-950">
      <ClassificationBanner level={classification} />

      <main className="flex-1 flex flex-col overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-800">
          <h1 className="text-xl font-bold text-white">Order of Battle</h1>
          <p className="text-sm text-gray-400 mt-0.5">
            Global military force structures — {countries?.length ?? '…'} nations
          </p>
        </div>

        <div className="flex flex-1 overflow-hidden">
          {/* Country list sidebar */}
          <aside className="w-72 border-r border-gray-800 flex flex-col overflow-hidden shrink-0">
            <div className="px-3 py-2 border-b border-gray-800">
              <p className="text-xs font-semibold uppercase tracking-wider text-gray-500">Countries</p>
            </div>

            {loadingCountries && (
              <div className="flex-1 flex items-center justify-center">
                <LoadingSpinner size="md" />
              </div>
            )}

            {countriesError && (
              <div className="p-4 text-sm text-red-400">Failed to load countries.</div>
            )}

            {countries && (
              <ul className="flex-1 overflow-y-auto divide-y divide-gray-800/50">
                {countries.map((country) => (
                  <li key={country.code}>
                    <button
                      onClick={() => setSelectedCountry(country)}
                      className={[
                        'w-full text-left px-3 py-2.5 flex items-center gap-2 text-sm transition-colors',
                        selectedCountry?.code === country.code
                          ? 'bg-sky-900/40 text-sky-300'
                          : 'text-gray-300 hover:bg-gray-800',
                      ].join(' ')}
                    >
                      <span className="text-base leading-none" aria-hidden>
                        {country.flag_emoji ?? '🏳️'}
                      </span>
                      <span className="flex-1 truncate font-medium">{country.name}</span>
                      <span className="text-xs text-gray-500 shrink-0">{country.code}</span>
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </aside>

          {/* Main content panel */}
          <div className="flex-1 overflow-y-auto p-6">
            {!selectedCountry && (
              <div className="h-full flex items-center justify-center text-gray-500 text-sm">
                Select a country to view its Order of Battle
              </div>
            )}

            {selectedCountry && (
              <div className="space-y-6">
                {/* Country header */}
                <div className="flex items-start gap-4">
                  <span className="text-5xl" aria-hidden>{selectedCountry.flag_emoji ?? '🏳️'}</span>
                  <div>
                    <h2 className="text-2xl font-bold text-white">{selectedCountry.name}</h2>
                    <p className="text-sm text-gray-400 mt-0.5">
                      {selectedCountry.region ?? 'Unknown region'} · {selectedCountry.code}
                      {selectedCountry.alliance_codes?.length > 0 && (
                        <span className="ml-2">
                          {selectedCountry.alliance_codes.map((a) => (
                            <span
                              key={a}
                              className="ml-1 inline-flex items-center rounded bg-sky-900/50 px-1.5 py-0.5 text-xs font-medium text-sky-300 ring-1 ring-sky-800"
                            >
                              {a}
                            </span>
                          ))}
                        </span>
                      )}
                    </p>
                  </div>
                </div>

                {/* Stats row */}
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                  <StatCard
                    label="Defense Budget"
                    value={formatBudget(selectedCountry.defense_budget_usd)}
                  />
                  <StatCard
                    label="Population"
                    value={formatPopulation(selectedCountry.population)}
                  />
                  <StatCard
                    label="GDP"
                    value={formatBudget(selectedCountry.gdp_usd)}
                  />
                </div>

                {/* Forces table */}
                <div>
                  <h3 className="text-base font-semibold text-white mb-3 flex items-center gap-2">
                    Military Units
                    {loadingForces && <LoadingSpinner size="sm" />}
                    {forces && (
                      <span className="text-xs font-normal text-gray-500">
                        ({forces.length} units on record)
                      </span>
                    )}
                  </h3>

                  {forces && forces.length === 0 && (
                    <p className="text-sm text-gray-500">No units on record for this country.</p>
                  )}

                  {forces && forces.length > 0 && (
                    <UnitsTable units={forces} />
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      </main>

      <ClassificationBanner level={classification} />
    </div>
  )
}

// ── sub-components ────────────────────────────────────────────────────────────

function StatCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-gray-800 bg-gray-900 px-4 py-3">
      <p className="text-xs text-gray-500 mb-0.5">{label}</p>
      <p className="text-sm font-semibold text-white">{value}</p>
    </div>
  )
}

function UnitsTable({ units }: { units: MilitaryUnit[] }) {
  return (
    <div className="overflow-x-auto rounded-lg border border-gray-800">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-gray-800 bg-gray-900">
            <th className="px-4 py-2 text-left text-xs font-semibold uppercase tracking-wider text-gray-500">Name</th>
            <th className="px-4 py-2 text-left text-xs font-semibold uppercase tracking-wider text-gray-500">Branch</th>
            <th className="px-4 py-2 text-left text-xs font-semibold uppercase tracking-wider text-gray-500">Echelon</th>
            <th className="px-4 py-2 text-left text-xs font-semibold uppercase tracking-wider text-gray-500">Class.</th>
            <th className="px-4 py-2 text-left text-xs font-semibold uppercase tracking-wider text-gray-500">Confidence</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-800/60">
          {units.map((unit) => (
            <tr key={unit.id} className="bg-gray-950 hover:bg-gray-900 transition-colors">
              <td className="px-4 py-2 text-white font-medium">{unit.name}</td>
              <td className="px-4 py-2">
                <BranchBadge branch={unit.branch} />
              </td>
              <td className="px-4 py-2 text-gray-400">{unit.echelon ?? '—'}</td>
              <td className="px-4 py-2 text-gray-400 text-xs">{unit.classification}</td>
              <td className="px-4 py-2 text-gray-400">
                {unit.confidence != null ? `${Math.round(unit.confidence * 100)}%` : '—'}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

const BRANCH_COLORS: Record<string, string> = {
  ARMY:        'bg-green-900/50 text-green-300 ring-green-800',
  NAVY:        'bg-blue-900/50 text-blue-300 ring-blue-800',
  AIR:         'bg-sky-900/50 text-sky-300 ring-sky-800',
  SPACE:       'bg-indigo-900/50 text-indigo-300 ring-indigo-800',
  CYBER:       'bg-yellow-900/50 text-yellow-300 ring-yellow-800',
  INTEL:       'bg-purple-900/50 text-purple-300 ring-purple-800',
  SPECIAL_OPS: 'bg-red-900/50 text-red-300 ring-red-800',
  COAST_GUARD: 'bg-teal-900/50 text-teal-300 ring-teal-800',
}

function BranchBadge({ branch }: { branch: string }) {
  const cls = BRANCH_COLORS[branch] ?? 'bg-gray-800 text-gray-300 ring-gray-700'
  return (
    <span className={`inline-flex items-center rounded px-1.5 py-0.5 text-xs font-medium ring-1 ${cls}`}>
      {branch}
    </span>
  )
}

// ── formatters ────────────────────────────────────────────────────────────────

function formatBudget(usd?: number): string {
  if (usd == null) return '—'
  if (usd >= 1e12) return `$${(usd / 1e12).toFixed(1)}T`
  if (usd >= 1e9) return `$${(usd / 1e9).toFixed(0)}B`
  if (usd >= 1e6) return `$${(usd / 1e6).toFixed(0)}M`
  return `$${usd}`
}

function formatPopulation(pop?: number): string {
  if (pop == null) return '—'
  if (pop >= 1e9) return `${(pop / 1e9).toFixed(1)}B`
  if (pop >= 1e6) return `${(pop / 1e6).toFixed(0)}M`
  return pop.toLocaleString()
}
