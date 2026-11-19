# AIT Bible

An AI translation of the Greek New Testament that shows its work.

The text aims to say in plain modern English what a first-century reader would have understood. It departs from the traditional English word only where that word now misleads, and every departure carries a note giving the traditional wording, the reason, and the standard scholarly view.

This is a machine translation. No scholar has reviewed it. Read it beside an established translation, not in place of one.

## How it works

- **The Greek source decides the verses.** The verse list comes from MorphGNT (SBLGNT). A chapter is rejected unless every verse is present exactly once.
- **A decision register keeps it consistent.** Each chapter is translated separately, so a short list of Greek words with one agreed rendering each is applied to all 260 chapters. See [translator/register.json](translator/register.json).
- **An audit checks the result.** After each run it counts how every register word was rendered across the whole New Testament; chapters that drift are re-translated.
- **A second model reviews every chapter.** A different model reads the Greek and the English side by side and reports omitted or added content and wrong meanings. Flagged verses are rewritten and reviewed again. Before it was trusted, the reviewer was tested on chapters with planted errors.
- **Everything is recorded.** Each run stores the model, prompt, register version and the raw output of every chapter under [translator/runs/](translator/runs/).

The current text was produced by `claude-fable-5-2` in run `20261118-224116-full-nt-2` under register 0.5, and reviewed by `claude-opus-5-5`.

## Examples

These are generated from the served text by `translator/build_glossary.py`. Each note is the translation's own.

**Matthew 16:18**

> KJV: And I say also unto thee, That thou art Peter, and upon this rock I will build my church; and the gates of hell shall not prevail against it.
>
> AIT: And I in turn tell you that you are Peter, and on this rock I will build my assembly, and the gates of Hades will not overpower it.
>
> Note on “assembly”: The nearly universal rendering is “church,” and readers know what it refers to. A first-century hearer, however, knew the word as a civic gathering and as the Greek Old Testament’s term for Israel assembled before God. “Church” now suggests a building or an institution, so “assembly” is used throughout this translation.

**Matthew 6:2**

> KJV: Therefore when thou doest thine alms, do not sound a trumpet before thee, as the hypocrites do in the synagogues and in the streets, that they may have glory of men. Verily I say unto you, They have their reward.
>
> AIT: So when you give to the needy, do not sound a trumpet ahead of you, as the performers do in the synagogues and in the streets, so that they may be praised by people. Truly I tell you, they have been paid their reward in full.
>
> Note on “performers”: The Greek word was the ordinary term for a stage actor, and in this passage the picture of a performance is active: a trumpet, street corners, an audience. Jewish Greek before the New Testament already used the word for a godless or insincere person, which is why most translations have “hypocrites” here. “Performers” is used in verses 2, 5 and 16 because the charge in each case is doing religion in order to be seen.

**Matthew 6:22**

> KJV: The light of the body is the eye: if therefore thine eye be single, thy whole body shall be full of light.
>
> AIT: The lamp of the body is the eye. So if your eye is generous, your whole body will be full of light;
>
> Note on “generous”: The Greek word means single or sincere, and related words are used of open-handed giving. The saying stands between treasure in heaven and slavery to wealth, and it is paired with the “evil eye”, a known idiom for stinginess, so “generous” fits the context. Most translations have “healthy” or “sound”, keeping the physical picture of an eye that lets in light, and mention generosity in a footnote; that picture is less visible in this rendering.

**Matthew 3:2**

> KJV: And saying, Repent ye: for the kingdom of heaven is at hand.
>
> AIT: and saying, “Turn back, for the kingdom of the heavens has come near.”
>
> Note on “Turn back”: The traditional rendering is “repent,” which most translations keep as an established term. In modern English “repent” centers on feeling sorry, whereas the Greek word, as used in the Gospels, carries the prophets’ call to return to God: a change of direction in mind and conduct. The related noun in verses 8 and 11 is rendered “turning back.”

**John 1:1**

> KJV: In the beginning was the Word, and the Word was with God, and the Word was God.
>
> AIT: In the beginning was the Logos, and the Logos was with God, and the Logos was God.
>
> Note on “Logos”: Nearly all translations render this “Word.” The Greek term covered speech, message, account and reason, and to many Greek-speaking readers it also suggested the rational principle that orders the world. Most scholars think John’s main background is the Hebrew Bible: God’s creating speech in Genesis 1, the “word of the Lord,” and the figure of Wisdom, which “Word” reflects and “Logos” does not. The Greek term is kept here as a title because “the Word” in current English usually means the Bible, which would give “the Word was God” a false sense.

## Repository

| Path | Contents |
|---|---|
| [translator/](translator/) | The translation pipeline, register, audit and run records. See its [README](translator/README.md). |
| [web/](web/) | Next.js site for reading the translation, with notes, Greek and a KJV comparison. |
| [schema/](schema/) | Description of the XML format the site reads. |

```bash
cd web && npm install && npm run dev
```

## Known limits

- No register entry has been checked against a lexicon, and no scholar has reviewed the text.
- The review pass catches blatant errors reliably (24 of 24 planted ones in testing). It has not been measured on subtle ones, and in the current run it flagged 3 verses out of 7,927, one of them as a major problem, which was rewritten.
- The KJV comparison uses a different Greek text, so some differences are textual and not translational.

## License

This project uses a dual-license approach:

### Software Code
**GNU GPL v3** - The code in this repository (Python scripts, web app, etc.) is licensed under the GNU General Public License v3.0. See [LICENSE](LICENSE) for details.

This means:
- ✅ You can use, modify, and distribute the code freely
- ✅ You can use it commercially
- ✅ **Any modifications must also be open source under GPL v3**
- ✅ Prevents proprietary forks - modifications must be shared back

This protects the project from being taken and commercialized without giving back to the community.

### Translation Output
**CC BY-NC-SA 4.0** - The English translation text produced by this software is licensed under [Creative Commons Attribution-NonCommercial-ShareAlike 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/).

This means the translation text:
- ✅ Can be shared and adapted for non-commercial purposes
- ✅ Requires attribution to AIT Bible Project
- ✅ Derivatives must use the same license
- ❌ Cannot be used commercially without permission

For commercial licensing of translations, please contact the project maintainers.

### Source Materials
- **SBLGNT Greek Text**: [CC BY 4.0](http://sblgnt.com/license/) © 2010 Logos Bible Software and Society of Biblical Literature
- **MorphGNT Data**: [CC BY-SA 3.0](https://github.com/morphgnt/sblgnt)
