"use client";

import { useState, useEffect, useRef } from "react";

const translationExamples = [
  {
    reference: "Matthew 5:5",
    traditional: {
      text: "Blessed are the meek, for they will inherit the earth.",
      highlight: "meek",
    },
    ait: {
      text: "Blessed are those gentle in strength, for they will inherit the earth.",
      highlight: "gentle in strength",
    },
    explanation:
      'The Greek *praeis* (πραεῖς) describes controlled strength, not weakness or passivity. Like a war horse trained for battle but responsive to its rider, it means having power but choosing restraint.',
  },
  {
    reference: "Matthew 6:5",
    traditional: {
      text: "And when you pray, you must not be like the hypocrites. For they love to stand and pray in the synagogues and at the street corners, that they may be seen by others.",
      highlight: "hypocrites",
    },
    ait: {
      text: "And when you pray, do not be like the performers, for they love to pray standing in the synagogues and at the corners of the main streets so that they may be seen by others.",
      highlight: "performers",
    },
    explanation:
      'The Greek *hypokritēs* (ὑποκριτής) meant "stage actor"—not someone morally inconsistent, but someone putting on a theatrical performance for an audience.',
  },
  {
    reference: "Matthew 6:22",
    traditional: {
      text: "The eye is the lamp of the body. If your eye is single, your whole body will be full of light.",
      highlight: "single",
    },
    ait: {
      text: "The eye is the lamp of the body. If your eye is generous, your whole body will be full of light.",
      highlight: "generous",
    },
    explanation:
      'The Greek *haplous* (ἁπλοῦς) invokes a Hebrew idiom where a "good eye" means generosity and an "evil eye" means stinginess. In context with Matthew 6\'s teaching on treasure and Mammon, this is about one\'s disposition toward wealth, not physical vision.',
  },
  {
    reference: "John 1:1",
    traditional: {
      text: "In the beginning was the Word, and the Word was with God, and the Word was God.",
      highlight: "Word",
    },
    ait: {
      text: "In the beginning was the Logos, and the Logos was with God, and the Logos was God.",
      highlight: "Logos",
    },
    explanation:
      '*Logos* (λόγος) carried meanings of reason, divine order, and the organizing principle of the cosmos, all nuances that "word" doesn\'t fully capture.',
  },
];

export function TranslationCarousel() {
  const [currentExample, setCurrentExample] = useState(0);
  const [fadeState, setFadeState] = useState<"fade-in" | "fade-out">("fade-in");
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  const startInterval = (duration = 8000) => {
    // Clear any existing interval
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
    }

    // Start a new interval
    intervalRef.current = setInterval(() => {
      setFadeState("fade-out");
      setTimeout(() => {
        setCurrentExample((prev) => (prev + 1) % translationExamples.length);
        setFadeState("fade-in");
      }, 500);
    }, duration);
  };

  useEffect(() => {
    startInterval();
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, []);

  return (
    <div className="relative mb-16 overflow-hidden">
      <div className="absolute inset-0 bg-linear-to-br from-amber-50 to-parchment-100 dark:from-amber-950/20 dark:to-neutral-900/50 rounded-2xl blur-3xl opacity-30" />
      <div className="relative card p-8 md:p-12">
        <div
          className={`transition-opacity duration-500 ${
            fadeState === "fade-in" ? "opacity-100" : "opacity-0"
          }`}
        >
          <div className="text-center mb-10">
            <span className="inline-block px-4 py-1.5 bg-amber-100 dark:bg-amber-900/30 text-amber-800 dark:text-amber-400 rounded-full text-xs font-sans font-semibold uppercase tracking-wider">
              {translationExamples[currentExample].reference}
            </span>
          </div>

          {/* Diff-Style Comparison */}
          <div className="space-y-3 mb-8">
            {/* Traditional - Red/Removed */}
            <div className="relative rounded-lg border-l-4 border-red-400 dark:border-red-600 bg-red-50 dark:bg-red-950/20 px-6 py-4">
              <div className="absolute -left-2 top-4 w-6 h-6 bg-red-100 dark:bg-red-900 border border-red-400 dark:border-red-600 rounded-full flex items-center justify-center">
                <span className="text-xs text-red-600 dark:text-red-400 font-mono font-bold">
                  -
                </span>
              </div>
              <span className="float-right ml-4 mb-2 text-xs text-red-600 dark:text-red-400 font-sans font-medium uppercase tracking-wider">
                Traditional
              </span>
              <p className="text-base md:text-lg text-neutral-700 dark:text-neutral-300">
                {translationExamples[currentExample].traditional.text
                  .split(
                    translationExamples[currentExample].traditional.highlight
                  )
                  .map((part, i, arr) => (
                    <span key={i}>
                      {part}
                      {i < arr.length - 1 && (
                        <span className="bg-red-200 dark:bg-red-900/50 text-red-900 dark:text-red-300 px-2 py-0.5 rounded font-semibold">
                          {
                            translationExamples[currentExample].traditional
                              .highlight
                          }
                        </span>
                      )}
                    </span>
                  ))}
              </p>
            </div>

            {/* AIT Translation - Green/Added */}
            <div className="relative rounded-lg border-l-4 border-emerald-400 dark:border-emerald-600 bg-emerald-50 dark:bg-emerald-950/20 px-6 py-4">
              <div className="absolute -left-2 top-4 w-6 h-6 bg-emerald-100 dark:bg-emerald-900 border border-emerald-400 dark:border-emerald-600 rounded-full flex items-center justify-center">
                <span className="text-xs text-emerald-600 dark:text-emerald-400 font-mono font-bold">
                  +
                </span>
              </div>
              <span className="float-right ml-4 mb-2 text-xs text-emerald-600 dark:text-emerald-400 font-sans font-medium uppercase tracking-wider">
                AIT
              </span>
              <p className="text-base md:text-lg text-neutral-900 dark:text-neutral-100">
                {translationExamples[currentExample].ait.text
                  .split(translationExamples[currentExample].ait.highlight)
                  .map((part, i, arr) => (
                    <span key={i}>
                      {part}
                      {i < arr.length - 1 && (
                        <span className="bg-emerald-200 dark:bg-emerald-900/50 text-emerald-900 dark:text-emerald-300 px-2 py-0.5 rounded font-semibold">
                          {translationExamples[currentExample].ait.highlight}
                        </span>
                      )}
                    </span>
                  ))}
              </p>
            </div>
          </div>

          {/* Explanation */}
          <div className="border-t border-neutral-200 dark:border-neutral-800 pt-6 mt-8">
            <p className="text-sm text-neutral-600 dark:text-neutral-400 leading-relaxed max-w-2xl mx-auto text-center">
              <svg
                className="w-4 h-4 text-amber-600 dark:text-amber-500 inline-block mr-1.5 -mt-0.5"
                fill="currentColor"
                viewBox="0 0 20 20"
              >
                <path
                  fillRule="evenodd"
                  d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z"
                  clipRule="evenodd"
                />
              </svg>
              {translationExamples[currentExample].explanation
                .split(/\*([^*]+)\*/g)
                .map((part, i) =>
                  i % 2 === 1 ? (
                    <em
                      key={i}
                      className="text-amber-700 dark:text-amber-500 font-semibold"
                    >
                      {part}
                    </em>
                  ) : (
                    part
                  )
                )}
            </p>
          </div>

          {/* Indicator dots */}
          <div className="flex justify-center gap-2 mt-6">
            {translationExamples.map((_, i) => (
              <button
                key={i}
                onClick={() => {
                  setFadeState("fade-out");
                  setTimeout(() => {
                    setCurrentExample(i);
                    setFadeState("fade-in");
                    startInterval(16000); // Give 2x time (16 seconds) for manual selections
                  }, 500);
                }}
                className={`w-2 h-2 rounded-full transition-all ${
                  i === currentExample
                    ? "bg-amber-600 dark:bg-amber-500 w-8"
                    : "bg-neutral-300 dark:bg-neutral-700 hover:bg-neutral-400 dark:hover:bg-neutral-600"
                }`}
                aria-label={`View ${translationExamples[i].reference}`}
              />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
