import { createFileRoute } from "@tanstack/react-router";
// @ts-expect-error - JS module
import CasesPage from "@/components/CasesPage";

export const Route = createFileRoute("/authority/cases")({
  head: () => ({
    meta: [
      { title: "Road Risk Cases — MargDrishti" },
      {
        name: "description",
        content: "Track assigned and in-progress road risk cases across highway hotspots.",
      },
      { property: "og:title", content: "Road Risk Cases — MargDrishti" },
      {
        property: "og:description",
        content: "Case queue for highway risk clusters flagged for field action.",
      },
    ],
  }),
  component: CasesPage,
});
