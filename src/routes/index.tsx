import { Link, createFileRoute } from '@tanstack/react-router'
import { useState } from 'react'
import wikigg from '@/assets/wiki.gg.json'
import { Command, CommandInput } from '@/components/ui/command'

export const Route = createFileRoute('/')({
  component: App,
})

function fuzzyMatchSequential(search: string, option: string) {
  const escapedSearchTerm = search.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
  const pattern = '.*' + escapedSearchTerm.split('').join('.*') + '.*'
  const regex = new RegExp(pattern, 'i')
  return regex.test(option)
}

function levenshteinDistance(s1: string, s2: string) {
  const len1 = s1.length
  const len2 = s2.length

  if (len1 === 0) return len2
  if (len2 === 0) return len1

  const matrix = []

  for (let i = 0; i <= len2; i++) {
    matrix[i] = [i]
  }
  for (let j = 0; j <= len1; j++) {
    matrix[0][j] = j
  }

  for (let i = 1; i <= len2; i++) {
    for (let j = 1; j <= len1; j++) {
      const cost = s2[i - 1] === s1[j - 1] ? 0 : 1
      matrix[i][j] = Math.min(
        matrix[i - 1][j] + 1,
        matrix[i][j - 1] + 1,
        matrix[i - 1][j - 1] + cost,
      )
    }
  }

  return matrix[len2][len1]
}

function App() {
  const [search, setSearch] = useState('')
  return (
    <div className="container mx-auto py-8 space-y-4">
      <Command>
        <CommandInput
          placeholder="Search..."
          onValueChange={(s) => setSearch(s)}
        />
      </Command>
      <div className="p-8 rounded-xl bg-gray-500">
        <div className="flex flex-wrap justify-center items-center gap-4">
          {wikigg
            .filter((wiki) => fuzzyMatchSequential(search, wiki.name))
            .sort(
              (a, b) =>
                levenshteinDistance(a.name, search) -
                levenshteinDistance(b.name, search),
            )
            .slice(0, 100)
            .map(
              (wiki) =>
                wiki.logo && (
                  <Link to="/$wiki" key={wiki.id} params={{ wiki: wiki.id }}>
                    <img
                      src={wiki.logo}
                      alt={wiki.name}
                      className="max-w-32 h-auto"
                    />
                  </Link>
                ),
            )}
        </div>
      </div>
    </div>
  )
}
