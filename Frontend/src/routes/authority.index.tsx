import { createFileRoute } from "@tanstack/react-router";
// @ts-expect-error - JS module
import AuthorityOverview from "@/components/AuthorityOverview";

export const Route = createFileRoute("/authority/")({
  head: () => ({
    meta: [
      { title: "Authority Overview — MargDrishti Road Risk Intelligence" },
      {
        name: "description",
        content:
          "Live map, risk clusters and analytics for high-risk road segments across Indian highways.",
      },
      { property: "og:title", content: "Authority Overview — MargDrishti" },
      {
        property: "og:description",
        content: "Monitor road risk hotspots, clusters and cases across Indian highways.",
      },
    ],
  }),
  component: AuthorityOverview,
});
