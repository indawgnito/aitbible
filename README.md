# AIT Bible

An AI translation of the Greek New Testament that shows its work.

The text aims to say in plain modern English what a first-century reader would have understood. It departs from the traditional English word only where that word now misleads, and every departure carries a note giving the traditional wording, the reason, and the standard scholarly view.

This is a machine translation. No scholar has reviewed it. Read it beside an established translation, not in place of one.

## How it works

- **The Greek source decides the verses.** The verse list comes from MorphGNT (SBLGNT). A chapter is rejected unless every verse is present exactly once.
- **A decision register keeps it consistent.** Each chapter is translated separately, so a short list of Greek words with one agreed rendering each is applied to all 260 chapters. See [translator/register.json](translator/register.json).
- **An audit checks the result.** After each run it counts how every register word was rendered across the whole New Testament; chapters that drift are re-translated.
- **Everything is recorded.** Each run stores the model, prompt, register version and the raw output of every chapter under [translator/runs/](translator/runs/).

The current text was produced by `claude-fable-5-2` in run `20261118-162954-full-nt`.

## Examples

These are generated from the served text by `translator/build_glossary.py`.

**Matthew 16:18**

> KJV: "And I say also unto thee, That thou art Peter, and upon this rock I will build my church; and the gates of hell shall not prevail against it."
>
> AIT: "And I in turn tell you: you are Peter, and on this rock I will build my assembly, and the gates of Hades will not overpower it."

The Greek *ekklēsia* was the word for a gathering of citizens, and in the Greek Old Testament for Israel assembled before God. "Church" now suggests a building or an institution. The same verse keeps *Hades*, the realm of the dead, where older versions have "hell".

**Matthew 6:2**

> KJV: "Therefore when thou doest thine alms, do not sound a trumpet before thee, as the hypocrites do in the synagogues and in the streets, that they may have glory of men. Verily I say unto you, They have their reward."
>
> AIT: "So when you give to the needy, do not sound a trumpet ahead of you, as the performers do in the synagogues and in the streets, so that people will praise them. Truly I tell you, they have been paid their reward in full."

In Matthew 6 the charge is religion staged for an audience, and the Greek word began as the term for a stage actor. Elsewhere, where the charge is pretense, this translation keeps "hypocrites": by the first century the word already meant that too. "Paid in full" is the wording of receipts from the period.

**Matthew 6:22**

> KJV: "The light of the body is the eye: if therefore thine eye be single, thy whole body shall be full of light."
>
> AIT: "The lamp of the body is the eye. So if your eye is generous, your whole body will be full of light;"

The saying sits between treasure in heaven and serving wealth, and the "evil eye" that follows was a Jewish idiom for stinginess. Most translations keep the physical image with "healthy" or "sound"; this one follows the idiom and says so in the note.

**Mark 1:15**

> KJV: "And saying, The time is fulfilled, and the kingdom of God is at hand: repent ye, and believe the gospel."
>
> AIT: "and saying, “The time has been fulfilled, and the kingdom of God has come near. Turn back, and believe in the good news.”"

"Repent" now centres on feeling sorry. The Greek carries the prophets' call to return to God: a change of direction. Most translations keep "repent" as an established term.

**John 1:1**

> KJV: "In the beginning was the Word, and the Word was with God, and the Word was God."
>
> AIT: "In the beginning was the Logos, and the Logos was with God, and the Logos was God."

Left untranslated because "the Word" is now commonly heard as meaning the Bible. The note at this verse gives both backgrounds: God's creating speech in Genesis, which most scholars see as primary and which "Word" reflects, and the Greek sense of reason and order.

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

- No second-pass review yet: an omitted clause inside a verse is only caught by a word-count warning.
- No register entry has been checked against a lexicon.
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
