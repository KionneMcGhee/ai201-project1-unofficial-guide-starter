"""Replay the recorded ChatGPT handoff, or request new completions with --engine groq."""
import argparse
import hashlib
import json
from dataclasses import asdict
from guide import Guide, INSTRUCTIONS, MEMORY, render
from ingest import ROOT
from search import Index

CHALLENGE = "Where did the Bison paper say I could take my laptop to juice it up at West?"
OUTSIDE = "What was the final score of the 1978 World Cup final?"


def signature(payload):
    serialized = json.dumps([INSTRUCTIONS,payload],ensure_ascii=False,sort_keys=True)
    return hashlib.sha256(serialized.encode()).hexdigest()


def main(engine):
    tests = json.loads((ROOT/"evaluation.json").read_text())
    captured = json.loads((ROOT/"handoff.json").read_text())
    index, fixed = Index(), Index("fixed")
    results = []
    for t in tests+[{"question":CHALLENGE},{"question":OUTSIDE}]:
        question=t["question"]
        def recorded(payload):
            return json.dumps(captured[signature(payload)])
        r=Guide(index).ask(question,engine,complete=recorded if engine=="handoff" else None)
        results.append({**t,"answer":r["answer"],"urls":render(r).splitlines()[len(r["answer"].splitlines()):],
                        "hits":[asdict(h) for h in r["hits"]]})
        if "anchors" in t:
            results[-1]["rankings"]={m:[h.id for h in index.search(question,m)] for m in ["semantic","bm25","hybrid"]}
            results[-1]["fixed"]=[asdict(h) for h in fixed.search(question)]
    return results


if __name__=="__main__":
    cli=argparse.ArgumentParser()
    cli.add_argument("--engine",choices=["handoff","groq","evidence"],default="handoff")
    args=cli.parse_args()
    print(json.dumps(main(args.engine),indent=2,ensure_ascii=False))
