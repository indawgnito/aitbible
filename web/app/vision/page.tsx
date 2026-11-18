import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "How It Was Made | AIT Bible",
  description:
    "How the AIT Bible is translated, what the notes mean, and what to be careful about",
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
        How It Was Made
      </h1>

      <div className="prose-reading space-y-8">
        <section>
          <h2 className="font-sans font-semibold text-2xl text-neutral-900 dark:text-neutral-100 mb-4">The aim</h2>
          <p>
            Words drift. &ldquo;Church&rdquo; now means a building or an
            institution; &ldquo;gospel&rdquo; means a kind of book or a kind
            of music. The Greek words behind them meant a gathering and an
            announcement of good news. This translation tries to say what a
            first-century reader of the Greek would have understood, judged
            by how words were used at the time and not by where they came
            from.
          </p>
          <p>
            It departs from the traditional English word only where that word
            now misleads. Where the traditional word is still the best one,
            it stays. Most of the text will sound familiar, and that is
            deliberate.
          </p>
        </section>

        <section>
          <h2 className="font-sans font-semibold text-2xl text-neutral-900 dark:text-neutral-100 mb-4">How the translation is produced</h2>
          <p>
            An AI model translates the Greek text of the SBL Greek New
            Testament one chapter at a time. The list of verses comes from
            the Greek source, and a chapter is rejected unless every verse is
            present exactly once.
          </p>
          <p>
            Because each chapter is translated separately, consistency comes
            from a <em>decision register</em>: a short list of Greek words
            with one agreed rendering each, applied to every chapter. After
            each run an audit counts how every one of those words was
            rendered across the whole New Testament, and chapters that drift
            are translated again.
          </p>
          <p>
            The register, the prompt, and the model&rsquo;s raw output for
            every chapter are in the{" "}
            <a href="https://github.com/indawgnito/aitbible" target="_blank" rel="noopener noreferrer" className="text-amber-700 dark:text-amber-500 hover:underline font-medium">
              repository
            </a>
            , so anyone can see why a word was chosen, change the decision,
            and run it again.
          </p>
        </section>

        <section>
          <h2 className="font-sans font-semibold text-2xl text-neutral-900 dark:text-neutral-100 mb-4">The notes</h2>
          <p>
            Wherever the text departs from the mainstream English tradition,
            a note gives the traditional rendering, the reason for the
            change, and the standard scholarly view, including when that view
            disagrees with the choice made here. Other notes mark places
            where the Greek is ambiguous, where manuscripts differ, or where
            a first-century reader knew something a modern reader needs.
            Click a verse number to see its notes and the Greek.
          </p>
          <p>
            Passages that the Greek edition prints in double brackets, such
            as the longer ending of Mark, are translated and kept in
            brackets, with a note explaining why they are doubted.
          </p>
        </section>

        <section>
          <h2 className="font-sans font-semibold text-2xl text-neutral-900 dark:text-neutral-100 mb-4">What to be careful about</h2>
          <p>
            This is a machine translation. No scholar has reviewed it, and
            the decisions in the register have not been checked against a
            lexicon. The model learned Greek from the same scholarship that
            produced existing translations, so it is not an independent
            authority, and it can be confidently wrong.
          </p>
          <p>
            Every translation makes choices, and this one does too. What it
            offers is that the choices are written down, applied
            consistently, and explained. Read it beside an established
            translation, not in place of one.
          </p>
          <p>
            The verse comparison shows the King James Version, which was
            translated from a different Greek text. Some differences you see
            there come from the manuscripts and not from translation choices.
          </p>
        </section>

        <section className="border-t border-neutral-200 dark:border-neutral-800 pt-8">
          <h2 className="font-sans font-semibold text-2xl text-neutral-900 dark:text-neutral-100 mb-4">Corrections</h2>
          <p>
            If you think a rendering or a note is wrong, open an issue on{" "}
            <a href="https://github.com/indawgnito/aitbible" target="_blank" rel="noopener noreferrer" className="text-amber-700 dark:text-amber-500 hover:underline font-medium">
              GitHub
            </a>
            . A change to the register is applied to every chapter where the
            word occurs.
          </p>
        </section>
      </div>
    </div>
  );
}
