import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Vision | AIT Bible",
  description:
    "Why we're using AI to retranslate the Bible from the original Greek",
};

export default function VisionPage() {
  return (
    <div className="container-reading py-16">
      {/* Breadcrumb */}
      <nav className="mb-8">
        <Link
          href="/"
          className="text-sm text-neutral-500 dark:text-neutral-400 hover:text-amber-700 dark:hover:text-amber-500 transition-colors font-sans"
        >
          ← Home
        </Link>
      </nav>

      {/* Page Title */}
      <h1 className="text-4xl md:text-5xl font-bold text-neutral-900 dark:text-neutral-100 mb-6">
        Our Vision
      </h1>

      <div className="prose-reading space-y-8">
        {/* Why This Exists */}
        <section>
          <h2 className="font-sans font-semibold text-2xl text-neutral-900 dark:text-neutral-100 mb-4">
            Why This Project Exists
          </h2>
          <p>
            Traditional Bible translations carry centuries of accumulated
            meaning—layers of interpretation that, while valuable, can obscure
            what the original audience would have understood. Words evolve.
            Contexts shift. What was clear to a first-century reader often
            becomes muddied by tradition.
          </p>
          <p>
            This project aims to cut through those layers and ask a simple
            question: <em>What did this actually mean to the people who first
            heard it?</em>
          </p>
        </section>

        {/* Examples */}
        <section>
          <h2 className="font-sans font-semibold text-2xl text-neutral-900 dark:text-neutral-100 mb-4">
            Translation Examples
          </h2>

          <div className="space-y-6">
            {/* Matthew 6 Example */}
            <div className="card p-6">
              <h3 className="font-sans font-semibold text-lg text-amber-700 dark:text-amber-500 mb-3">
                Matthew 6: "Performers" vs. "Hypocrites"
              </h3>
              <p>
                In Matthew 6, traditional translations use the word{" "}
                <strong>"hypocrites"</strong> to describe those who pray and
                give alms publicly for recognition. Today, "hypocrite" implies
                someone who says one thing but does another—a moral
                inconsistency.
              </p>
              <p>
                But the original Greek word <em>hypokritēs</em> (ὑποκριτής)
                meant <strong>"stage actor"</strong> or{" "}
                <strong>"performer"</strong>. Jesus wasn't primarily condemning
                moral inconsistency—he was critiquing theatrical religious
                performance. These were people putting on a show, playing a
                role for an audience. That nuance changes everything.
              </p>
              <p className="text-sm text-neutral-600 dark:text-neutral-400 mt-4">
                Our translation uses "performers" to recover that original
                theatrical imagery.
              </p>
            </div>

            {/* John 1 Example */}
            <div className="card p-6">
              <h3 className="font-sans font-semibold text-lg text-amber-700 dark:text-amber-500 mb-3">
                John 1: "Word" vs. "Logos"
              </h3>
              <p>
                The opening of John's Gospel is one of the most famous passages
                in the Bible: <em>"In the beginning was the Word, and the Word
                was with God, and the Word was God."</em>
              </p>
              <p>
                The problem? <strong>"Word"</strong> is a profoundly
                insufficient translation of <em>logos</em> (λόγος). To
                Greek-speaking readers, <em>logos</em> meant far more than just
                "word"—it carried connotations of reason, divine order, the
                organizing principle of the cosmos, the rational structure
                underlying reality.
              </p>
              <p>
                Philosophers like Heraclitus and the Stoics used{" "}
                <em>logos</em> to describe the fundamental rationality that
                governs the universe. When John's audience heard{" "}
                <em>logos</em>, they understood it as a profound theological
                claim: the ordering principle of all existence had become flesh.
              </p>
              <p>
                Translating it simply as "word" flattens that rich, layered
                meaning into something far more pedestrian.
              </p>
              <p className="text-sm text-neutral-600 dark:text-neutral-400 mt-4">
                Our translation acknowledges this complexity and provides notes
                explaining the fuller meaning of <em>logos</em>.
              </p>
            </div>
          </div>
        </section>

        {/* Why AI? */}
        <section>
          <h2 className="font-sans font-semibold text-2xl text-neutral-900 dark:text-neutral-100 mb-4">
            Why Use AI for Translation?
          </h2>
          <p>
            Language is AI's native domain. Modern language models can hold the
            entirety of multiple languages in context simultaneously—ancient
            Greek, classical philosophy, historical usage patterns, semantic
            relationships across millennia. They can identify subtle meanings
            that get lost in word-for-word translation.
          </p>
          <p>
            Where human translators must make judgment calls based on their
            training and theological traditions, AI can analyze the full
            semantic range of a word, compare it to how it was used in
            contemporary literature, and offer translations that prioritize
            original meaning over inherited tradition.
          </p>
          <p>
            This doesn't make AI perfect—but it makes it exceptionally
            well-suited for the task of linguistic analysis.
          </p>
        </section>

        {/* Limitations */}
        <section>
          <h2 className="font-sans font-semibold text-2xl text-neutral-900 dark:text-neutral-100 mb-4">
            Acknowledging AI's Limitations
          </h2>
          <p>
            We recognize that AI has inherent limitations. Language models are
            trained on human data, which means they can carry the same biases,
            assumptions, and blind spots that humans do. There's also a risk
            that AI might default to producing translations similar to existing
            versions—simply because those versions dominate its training data.
          </p>
          <p>
            This project is not about replacing human scholarship. It's about
            augmenting it. AI gives us a powerful tool for re-examining
            long-held assumptions and recovering meanings that tradition may
            have obscured. But it's a tool, not an oracle.
          </p>
          <p>
            We approach this work with humility, transparency, and a commitment
            to explaining our translation choices. Each chapter includes
            detailed notes on significant decisions, so you can see our
            reasoning and decide for yourself.
          </p>
        </section>

        {/* Call to Action */}
        <section className="border-t border-neutral-200 dark:border-neutral-800 pt-8">
          <h2 className="font-sans font-semibold text-2xl text-neutral-900 dark:text-neutral-100 mb-4">
            An Ongoing Project
          </h2>
          <p>
            This is an open-source effort. The code, the translations, and the
            methodology are all available for anyone to review, critique, and
            improve. We believe that transparency and collaboration produce
            better results than closed systems.
          </p>
          <p>
            If you find this work valuable—or if you have questions,
            critiques, or suggestions—we'd love to hear from you. Check out the{" "}
            <a
              href="https://github.com/indawgnito/aitbible"
              target="_blank"
              rel="noopener noreferrer"
              className="text-amber-700 dark:text-amber-500 hover:underline font-medium"
            >
              GitHub repository
            </a>{" "}
            to learn more or contribute.
          </p>
        </section>
      </div>
    </div>
  );
}
