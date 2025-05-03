import { createFileRoute } from '@tanstack/react-router'
import wikigg from '@/assets/wiki.gg.json'

export const Route = createFileRoute('/$wiki')({
  component: RouteComponent,
})

function RouteComponent() {
  const params = Route.useParams()
  const data = wikigg.find((wiki) => wiki.id == params.wiki)
  return <iframe className="w-full aspect-video" src={data?.host} />
}
