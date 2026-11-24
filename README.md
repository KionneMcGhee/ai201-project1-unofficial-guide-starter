# The Unofficial Howard Guide

A student asks where to meet a study group in Towers West. Searching for the building alone also turns up its convenience store. This guide searches Howard student reporting for the passage that answers the question and shows the article, publication date and evidence ID beside the answer.

[Watch the narrated project demo](demo.mp4) · [Design and evaluation plan](planning.md)

## Run the guide

Unzip the folder and open a terminal in the directory containing `guide.py`. Python 3.10 or newer runs the included indexes, CLI and evaluation with its standard library.

```sh
python3 guide.py
python3 guide.py --show-hits "Which two dining halls accepted meal swipes in the 2026–27 report?"
python3 evaluate.py
```

**Live LLM mode.** Set the environment variable `GROQ_API_KEY` to a Groq key in your shell. Run `python3 guide.py --engine groq`. The client sends the question and four retrieved passages to Groq's chat completions endpoint. Its default model is `llama-3.3-70b-versatile`. Set `GROQ_MODEL` to another available JSON-capable model to change it. The CLI reads environment variables directly. Keep credentials out of the project. Run `python3 evaluate.py --engine groq` for new live model outputs. This path requires internet access and a valid API key.

**Key-free modes.** The default without a key is `evidence`, which displays the highest-ranked source passage. It is an extractive baseline. For a fresh model answer, `--engine handoff` prints the grounding instructions and the exact context to give an LLM, then accepts its single-line JSON response. The recorded evaluation below used this ChatGPT handoff. The automated Groq connection was not exercised in the recorded run.

**Rebuild.** The SQLite files contain the fitted embeddings and passage metadata. To regenerate both indexes after changing documents, install NumPy in a virtual environment and run the build command.

```sh
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
python3 search.py --build
```

## Domain and document sources

The collection covers study spaces, meals, groceries and neighborhood gathering places as described by Howard’s student newspaper, *The Hilltop*. A campus directory can tell a reader that Towers West exists. A student guide can tell them which room was photographed as the largest. All answers describe the dates shown in their citations. The collection includes selected reporting details and individual experiences.

Each local text file contains independently worded notes drawn from its linked article. These passages are the indexed source text. They preserve the publication’s reporting without distributing full copies of articles.

| Local file | Publication date | Original article |
|---|---|---|
| [documents/study.txt](documents/study.txt) | 2023-08-21 | [Best Places to Study on Campus](https://thehilltoponline.com/2023/08/21/best-places-to-study-on-campus/) |
| [documents/founders.txt](documents/founders.txt) | 2026-02-16 | [Founders Library Reveals New Study Space](https://thehilltoponline.com/2026/02/16/founders-library-reveals-new-study-space/) |
| [documents/pantry.txt](documents/pantry.txt) | 2023-11-06 | [New Food Pantry Aims to Tackle Food Insecurity at Howard](https://staging.thehilltoponline.com/2023/11/06/new-food-pantry-aims-to-tackle-food-insecurity-at-howard/) |
| [documents/groceries.txt](documents/groceries.txt) | 2022-08-15 | [Where to Shop Without Mom and Pop](https://thehilltoponline.com/2022/08/15/where-to-shop-without-mom-and-pop/) |
| [documents/closures.txt](documents/closures.txt) | 2025-09-08 | [Georgia Ave Restaurant Closures Leave Students Asking: What is Left to Eat?](https://thehilltoponline.com/2025/09/08/georgia-ave-restaurant-closures-leave-students-asking-what-is-left-to-eat/) |
| [documents/artivism.txt](documents/artivism.txt) | 2025-10-06 | [Sankofa Hosts Weekly “Artivism” Jam Sessions](https://thehilltoponline.com/2025/10/06/sankofa-hosts-weekly-artivism-jam-sessions/) |
| [documents/guide.txt](documents/guide.txt) | 2025-08-18 | [A Beginner’s Guide to Washington, D.C., According to Bison](https://thehilltoponline.com/2025/08/18/a-beginners-guide-to-washington-d-c-according-to-bison/) |
| [documents/georgia.txt](documents/georgia.txt) | 2026-08-31 | [Ethiopian Businesses Build Community Along Georgia Avenue](https://thehilltoponline.com/2026/08/31/ethiopian-businesses-build-community-along-georgia-avenue/) |
| [documents/plans.txt](documents/plans.txt) | 2026-08-17 | [Howard Introduces New Meal Plans for 2026-27 School Year](https://thehilltoponline.com/2026/08/17/howard-introduces-new-meal-plans-for-2026-27-school-year/) |
| [documents/aramark.txt](documents/aramark.txt) | 2025-09-02 | [New Dining Experience: Aramark Collegiate Hospitality](https://thehilltoponline.com/2025/09/02/new-dining-experience-aramark-collegiate-hospitality/) |

## Document pipeline and chunking

`ingest.py` reads the ten UTF-8 text files named in the source registry, normalizes Unicode, splits at blank lines and collapses whitespace. Collection excluded menus, ads, bylines, related-story links and photo credits. The local notes retain substantive details from captions, such as the identifier P-42. Each passage carries its file ID, position, title and publication date through the source registry.

The primary splitter targets **one observation per paragraph**, capped at **75 whitespace tokens**. Distinct paragraphs have **zero overlap**. Oversized paragraphs use 75-token windows with **12 tokens of overlap**. The cap allows a location and access condition to stay together. The included paragraphs already fit under the cap. These ten short source files produce **27 chunks**. Splitting to reach an arbitrary count would separate facts such as the grocery address and its pharmacy. The comparison below measures that effect.

## Sample chunks

**Chunk 1 · study-01 · documents/study.txt**

> Howard Plaza Towers West offered both small study rooms and larger spaces for group work. The guide placed them on the right side of the first floor. Its photograph identified P-42 as the largest study room in the building.

**Chunk 2 · pantry-01 · documents/pantry.txt**

> In November 2023, The Store @ HU operated on the first floor of Blackburn University Center. Students booked an appointment to visit the pantry.

**Chunk 3 · artivism-01 · documents/artivism.txt**

> At the time of the October 2025 report, Sankofa hosted the Artivism jam on Tuesday nights. Howard alumni Joshua Hughes and Isaac Alicea hosted the sessions.

**Chunk 4 · plans-01 · documents/plans.txt**

> For the 2026–27 academic year, the article identified Blackburn Café and Bethune Annex Café as the two dining halls students could enter with meal swipes.

**Chunk 5 · groceries-02 · documents/groceries.txt**

> The guide listed Giant Food at 1345 Park Road NW in Columbia Heights. It highlighted the supermarket's pharmacy and regular promotions.

## Embedding model and retrieval

The embedding model is **16-dimensional latent semantic analysis (LSA)**, fitted to this corpus. It weights word counts by sublinear TF and smoothed IDF, normalizes each row and takes the leading 16 right singular vectors. The same vocabulary, weights and projection encode new questions. A read-only SQLite connection loads vectors for an exact cosine scan. The primary index has 27 vectors. The alternate index fits its own projection across 61 chunks.

A corpus-trained model is small enough to ship with the guide, keeps queries local during retrieval and has no per-query fee. A model trained on ten sources has little evidence for unfamiliar synonyms. A production decision would compare this model with a pretrained sentence encoder on held-out student phrasing, acronyms and multilingual queries. Measure evidence recall, memory, index rebuild time, end-to-end latency and API costs. Longer model context matters if whole articles replace the short notes.

### Three retrieval tests

Each table is a real hybrid search. Higher hybrid scores rank earlier. Cosine distance is 1 minus cosine similarity. Semantic distance and hybrid score use different scales.

**Which room did the 2023 study guide identify as the largest study room in Towers West?**

| Rank | Chunk | Hybrid | Cosine distance | Returned text |
|---:|---|---:|---:|---|
| 1 | study-01 | 0.985 | 0.025 | Howard Plaza Towers West offered both small study rooms and larger spaces for group work. The guide placed them on the right side of the first floor. Its photograph identified P-42 as the largest study room in the building. |
| 2 | groceries-01 | 0.548 | 0.393 | The 2022 grocery guide placed The Market in the lobby of Howard Plaza Towers West. Students could pick up packaged snacks and cleaning supplies there. |
| 3 | study-02 | 0.527 | 0.345 | The 2023 article said students could reserve group rooms in the Undergraduate Library from a phone or computer. The library also had individual study rooms, printers and desktop computers. |
| 4 | study-04 | 0.263 | 0.652 | The Stacks provided a quieter place to work among the books inside Founders Library. Louis Stokes Library offered a choice between quiet areas and places where study partners could talk. |

The first passage identifies the room in a photo caption. The runner-up matches Towers West but discusses its store. A shared building name alone would give the wrong answer.

**In the 2023 report, where was The Store @ HU and how did students visit?**

| Rank | Chunk | Hybrid | Cosine distance | Returned text |
|---:|---|---:|---:|---|
| 1 | pantry-01 | 0.949 | 0.086 | In November 2023, The Store @ HU operated on the first floor of Blackburn University Center. Students booked an appointment to visit the pantry. |
| 2 | pantry-02 | 0.607 | 0.324 | The Store @ HU carried food, hygiene products and school supplies. The report described support from faculty, staff and alumni. |
| 3 | pantry-03 | 0.285 | 0.525 | The Blackburn pantry was the second food pantry discussed in the article. The earlier pantry was in College Hall South. |
| 4 | study-02 | 0.271 | 0.674 | The 2023 article said students could reserve group rooms in the Undergraduate Library from a phone or computer. The library also had individual study rooms, printers and desktop computers. |

The first passage pairs the floor with the appointment requirement. The next two passages describe the same pantry, but inventory and the older pantry’s location cannot answer both parts.

**Which night was the Sankofa Artivism jam, and who hosted it in October 2025?**

| Rank | Chunk | Hybrid | Cosine distance | Returned text |
|---:|---|---:|---:|---|
| 1 | artivism-01 | 0.984 | 0.027 | At the time of the October 2025 report, Sankofa hosted the Artivism jam on Tuesday nights. Howard alumni Joshua Hughes and Isaac Alicea hosted the sessions. |
| 2 | guide-02 | 0.685 | 0.184 | The August 2025 guide traced the alumni's weekly jam sessions and open mics at Sankofa back to 2023. The graduates ran the events through their Artivism group. |
| 3 | artivism-02 | 0.277 | 0.718 | Performers at the Sankofa jam could share poems or songs. A backing band played saxophone, drums, piano and bass. |
| 4 | guide-01 | 0.236 | 0.674 | Two recent Howard graduates described spending time at Sankofa Video Books and Café. The guide placed it on Georgia Avenue about five minutes on foot from the Yard. |

The October story supplies the weekday and both hosts. The August story also describes the jam, which explains its high rank, but its passage does not name the hosts.

## Grounded generation and interface

The generator receives only the question, the retrieved IDs, titles, dates and text, plus the prior question for an explicit follow-up. The model must select complete supporting sentences and return their IDs as JSON. The app checks that each ID was retrieved and that its quote occurs in that specific passage. An invalid ID or unsupported quote produces a refusal. The app attaches the title, date and URL itself. These checks establish provenance. They cannot guarantee that a cited sentence answers the question. A preliminary gate also refuses when the top passage has zero BM25 support or cosine similarity below 0.28.

The CLI accepts a question, an optional source ID (`--source`), a retrieval method (`--method`) and an answer engine (`--engine`). Output contains the answer and citations, followed by the original publication URLs. `--show-hits` reveals retrieval scores and the text considered. Use `/quit` to leave a chat.

**One complete CLI exchange · local evidence mode**

```text
You > Which room did the 2023 study guide identify as the largest study room in Towers West?
Howard Plaza Towers West offered both small study rooms and larger spaces for group work. The guide placed them on the right side of the first floor. Its photograph identified P-42 as the largest study room in the building. [Best Places to Study on Campus, 2023-08-21, study-01]
https://thehilltoponline.com/2023/08/21/best-places-to-study-on-campus/
```

## Evaluation report

The five questions and expected answers were recorded before implementation. The saved LLM responses are keyed by a hash of the actual prompt and complete retrieved context. Running `evaluate.py` retrieves the passages again, validates the matching responses through the same answer pipeline, and prints the results. Any context change invalidates the saved response. New Groq runs may differ.

### 1. Which room did the 2023 study guide identify as the largest study room in Towers West?

**Expected.** P-42 in Howard Plaza Towers West.

**Actual.** Its photograph identified P-42 as the largest study room in the building. [Best Places to Study on Campus, 2023-08-21, study-01]

**Judgment.** Accurate. The cited sentence identifies P-42.

### 2. In the 2023 report, where was The Store @ HU and how did students visit?

**Expected.** The first floor of Blackburn University Center, by appointment.

**Actual.** In November 2023, The Store @ HU operated on the first floor of Blackburn University Center. Students booked an appointment to visit the pantry. [New Food Pantry Aims to Tackle Food Insecurity at Howard, 2023-11-06, pantry-01]

**Judgment.** Accurate. Both the location and booking requirement are present.

### 3. Which night was the Sankofa Artivism jam, and who hosted it in October 2025?

**Expected.** Tuesday nights, hosted by Joshua Hughes and Isaac Alicea.

**Actual.** At the time of the October 2025 report, Sankofa hosted the Artivism jam on Tuesday nights. Howard alumni Joshua Hughes and Isaac Alicea hosted the sessions. [Sankofa Hosts Weekly “Artivism” Jam Sessions, 2025-10-06, artivism-01]

**Judgment.** Accurate. The answer gives Tuesday and both full names.

### 4. Which two dining halls accepted meal swipes in the 2026–27 report?

**Expected.** Blackburn Café and Bethune Annex Café.

**Actual.** For the 2026–27 academic year, the article identified Blackburn Café and Bethune Annex Café as the two dining halls students could enter with meal swipes. [Howard Introduces New Meal Plans for 2026-27 School Year, 2026-08-17, plans-01]

**Judgment.** Accurate. It identifies both cafés within the requested academic year.

### 5. What was the street number of the supermarket with a dispensary in the 2022 shopping guide?

**Expected.** 1345, the Giant Food address on Park Road NW. The article uses the word pharmacy.

**Actual.** The guide listed Giant Food at 1345 Park Road NW in Columbia Heights. It highlighted the supermarket's pharmacy and regular promotions. [Where to Shop Without Mom and Pop, 2022-08-15, groceries-02]

**Judgment.** Accurate. The passage identifies the street number and confirms the pharmacy clue.

**Result.** Five of five planned questions were accurate. This is a small, source-aware test set. It measures these examples only.

### Additional failure case · missing information during ingestion

**Question.** Where did the Bison paper say I could take my laptop to juice it up at West?

**Expected.** The first-floor study rooms on the right in Towers West had conveniently placed outlets, according to the original 2023 study guide.

**Actual.** I don't have enough information in the retrieved reporting to answer that.

**Judgment.** Inaccurate against the original article. Refusal was appropriate given the available notes. Hybrid search ranked `groceries-01` first and `study-01` second. The latter describes the rooms and their location but omits the outlets mentioned in the article. The phrase “juice it up” also retrieved two passages about a juice bar. Even perfect reranking could not restore the missing fact. A targeted fix would add the outlet detail during ingestion and retest this question alongside a literal “power outlet” version. [Original study guide](https://thehilltoponline.com/2023/08/21/best-places-to-study-on-campus/)

### Out-of-scope control

**Question.** What was the final score of the 1978 World Cup final?

**Actual.** I don't have enough information in the retrieved reporting to answer that.

The query had no matching indexed terms after preprocessing. The gate stopped it before generation, with no cited source.

## Stretch results

### Hybrid search

BM25 uses k1 = 1.2 and b = 0.75. For each eligible set of passages, divide each BM25 score by the highest BM25 score (use zero when all scores are zero). The hybrid value is 0.60 times nonnegative cosine similarity plus 0.40 times normalized BM25. The standalone semantic and keyword modes use their original scores. The three comparisons show all four retrieved IDs in rank order.

| Query | Semantic only | BM25 only | Hybrid |
|---|---|---|---|
| Q1 | study-01, study-02, groceries-01, study-04 | study-01, groceries-01, study-02, pantry-01 | study-01, groceries-01, study-02, study-04 |
| Q2 | pantry-01, pantry-02, pantry-03, study-02 | pantry-01, pantry-02, guide-02, study-02 | pantry-01, pantry-02, pantry-03, study-02 |
| Q3 | artivism-01, guide-02, guide-01, artivism-03 | artivism-01, guide-02, artivism-02, artivism-03 | artivism-01, guide-02, artivism-02, guide-01 |

All three methods tied for first-place answer-bearing retrieval on these three questions (3/3 each). Differences appeared lower down. For Q1, keyword and hybrid promoted the geographically related store to second place. Semantic ranked another study passage second. For Q3, hybrid ranked a passage about the jam’s performers third, while semantic ranked a general café description third. These rankings support keeping hybrid as an option. They do not establish an overall accuracy gain.

### Chunking comparison

This comparison reruns the same five queries with hybrid retrieval and scores whether the top chunk contains **all** predefined answer strings. It measures evidence completeness at rank one. Matching is case-insensitive.

| Query | Paragraph result | All answer strings? | Fixed 12-token result | All answer strings? |
|---|---|---|---|---|
| Q1 | study-01 | Yes | study-03 · the first floor. Its photograph identified P-42 as the largest study room | Yes |
| Q2 | pantry-01 | Yes | pantry-01 · In November 2023, The Store @ HU operated on the first floor | No |
| Q3 | artivism-01 | Yes | artivism-01 · At the time of the October 2025 report, Sankofa hosted the Artivism | No |
| Q4 | plans-01 | Yes | plans-03 · swipes. Howard eliminated dining dollars in the 2026–27 meal plan revision. The | No |
| Q5 | groceries-02 | Yes | groceries-04 · Columbia Heights. It highlighted the supermarket's pharmacy and regular promotions. The article | No |

Paragraphs scored 5/5 and fixed windows scored 1/5. Q1's short identifier survived. In Q2 the fixed window ends at “first floor,” losing both the building name and the appointment requirement. In Q5 the fixed window retrieves the pharmacy clue while the street number sits elsewhere. A generated answer needs these facts together.

### Source metadata filter

For Q3, unrestricted hybrid search starts with `artivism-01`. Running the same query with `--source guide` returns only `guide-02` and `guide-01`. Filtering happens before ranking. The source filter narrows what the user can cite, even if a different article answers the question better.

### Conversational memory

The follow-up selects the most recent cited article and excludes already cited passages. The new question contains no event or venue names. A new session has no article to resolve.

```text
You > Which night was the Sankofa Artivism jam, and who hosted it in October 2025?
At the time of the October 2025 report, Sankofa hosted the Artivism jam on Tuesday nights. Howard alumni Joshua Hughes and Isaac Alicea hosted the sessions. [Sankofa Hosts Weekly “Artivism” Jam Sessions, 2025-10-06, artivism-01]
https://thehilltoponline.com/2025/10/06/sankofa-hosts-weekly-artivism-jam-sessions/
You > What else does that article say?
Performers at the Sankofa jam could share poems or songs. A backing band played saxophone, drums, piano and bass. [Sankofa Hosts Weekly “Artivism” Jam Sessions, 2025-10-06, artivism-02]
https://thehilltoponline.com/2025/10/06/sankofa-hosts-weekly-artivism-jam-sessions/

Fresh session
You > What else does that article say?
Ask a question first so I know which article you mean.
```

## Spec reflection

Planning the evaluation around paired facts, such as the pantry’s floor and the appointment rule, gave the project a concrete way to compare chunk sizes. Comparing only whether a result came from the correct article would have hidden the fixed-window failures.

The spec originally described one generation stage. The implementation adds a local extractive mode and a JSON handoff so a grader can inspect live retrieval and reproduce model outputs without an API account. The tradeoff is explicit in the interface. Extractive mode returns a whole passage and can surface a related passage on a difficult question. The model-backed modes can decline an unsupported inference.
