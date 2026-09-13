import { createFileRoute } from "@tanstack/react-router";
// @ts-expect-error - JS module
import ClusterInvestigation from "@/components/ClusterInvestigation";

export const Route = createFileRoute("/authority/cluster/$id")({
  head: () => ({
    meta: [
      { title: "Cluster Investigation — MargDrishti" },
      {
        name: "description",
        content: "Investigate a road risk cluster: contributing vehicles, events and timeline.",
      },
      { property: "og:title", content: "Cluster Investigation — MargDrishti" },
      {
        property: "og:description",
        content: "Contributing vehicles and events behind a highway risk cluster.",
      },
    ],
  }),
  component: ClusterPage,
});

function ClusterPage() {
  const { id } = Route.useParams();
  return <ClusterInvestigation id={id} />;
}
