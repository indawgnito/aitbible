import { Metadata } from "next";
import {
  glossaryTerms,
  glossaryCategories,
  type GlossaryTerm,
} from "@/lib/glossary";
import { GlossaryContent } from "./GlossaryContent";

export const metadata: Metadata = {
  title: "Word Choices | AIT Bible",
  description:
    "The words where the AIT Bible departs from the traditional English rendering, with the reason and the standard scholarly view.",
};

export default function GlossaryPage() {
  // Sort terms alphabetically within each category
  const categoryOrder = Object.keys(glossaryCategories);

  const termsByCategory: Record<string, GlossaryTerm[]> = {};
  for (const catId of categoryOrder) {
    const terms = glossaryTerms
      .filter((t) => t.category === catId)
      .sort((a, b) =>
        a.aitRendering.localeCompare(b.aitRendering, undefined, {
          sensitivity: "base",
        })
      );
    if (terms.length > 0) {
      termsByCategory[catId] = terms;
    }
  }

  const categories = categoryOrder
    .filter((id) => termsByCategory[id])
    .map((id) => ({
      id,
      name: glossaryCategories[id].name,
      description: glossaryCategories[id].description,
      count: termsByCategory[id].length,
    }));

  return (
    <GlossaryContent
      categories={categories}
      termsByCategory={termsByCategory}
    />
  );
}
