# Spotting low-quality transcribers from data signals

A speech-data platform pre-fills each audio clip with an AI (Whisper) transcript, and human transcribers correct it. The question: which data signals show that someone isn't doing the work, and how could a system act on them without wrongly blocking honest people?

**Report:** [Transcriber_Quality_Report.pdf](Transcriber_Quality_Report.pdf) · **Code:** [transcriber_quality.py](transcriber_quality.py)

## What I found (51,783 tasks)

- **Strongest signal:** keeping the AI draft unchanged while spending less time than the audio lasts. On 223 clips transcribed by several people, 85% of these submissions disagreed with the other transcribers, against 16% for everything else.
- **Time that ignores clip length:** for normal work, time spent rises with audio length (correlation 0.55). For the flagged users it doesn't (about 0), and most long clips are finished faster than real time. Their timings also look like a possible logging artefact, which is exactly why time alone should never trigger a block.
- **Kept hallucinations:** when the AI repeats one word for a whole clip, submitting it unchanged is near-certain proof of not listening.
- **Data check first:** the provided characters-per-second field turned out to be based on audio length, not time taken, and only 10 user IDs had more than one task, so I used the rest as a baseline.

## Proposed system

Signals decide **who gets checked more**; hidden clips with known transcripts decide **who gets blocked**. Watch → more known-answer clips → warning and payment hold → block only if known-answer accuracy stays low, a warning sign persists over 30+ tasks, and a human reviewer agrees. Product asks: log real audio playback, require playback before submit, tag buttons instead of free text, and show transcribers their own accuracy.

The dataset belongs to the platform and is not included. Run with: `python transcriber_quality.py <dataset.xlsx>`.
