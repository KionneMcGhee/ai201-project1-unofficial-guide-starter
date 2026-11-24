"""Exact vector search over a small SQLite collection. NumPy is needed only to rebuild."""
import argparse
import json
import math
import re
import sqlite3
from collections import Counter
from dataclasses import dataclass
from ingest import ROOT, chunks

STOP = set("a an the in of for as to and or which what when where how did is was were it on at with by from its students article guide report reported who me tell about does do their this that".split())


def tokens(text):
    return [w for w in re.findall(r"[a-z0-9]+", text.casefold()) if w not in STOP]


def normalize(v):
    length = math.sqrt(sum(x*x for x in v))
    return [x/length for x in v] if length else list(v)


def dot(a, b):
    return sum(x*y for x, y in zip(a, b))


def build(strategy):
    import numpy as np
    rows = list(chunks(strategy))
    counts = [Counter(tokens(r[3])) for r in rows]
    vocab = sorted(set().union(*(c.keys() for c in counts)))
    df = {t:sum(t in c for c in counts) for t in vocab}
    idf = {t:1+math.log((len(rows)+1)/(df[t]+1)) for t in vocab}
    matrix = np.array([normalize([(1+math.log(c[t]))*idf[t] if c[t] else 0 for t in vocab]) for c in counts])
    _, _, vt = np.linalg.svd(matrix, full_matrices=False)
    projection = vt[:16].T
    # A single transaction keeps the old index usable if a rebuild fails.
    with sqlite3.connect(ROOT / f"{strategy}.sqlite") as db:
        db.execute("CREATE TABLE IF NOT EXISTS model(term PRIMARY KEY, idf, vector)")
        db.execute("CREATE TABLE IF NOT EXISTS passages(id PRIMARY KEY, source, position, text, vector)")
        db.execute("DELETE FROM model")
        db.execute("DELETE FROM passages")
        db.executemany("INSERT INTO model VALUES (?,?,?)", [(t,idf[t],json.dumps(v.tolist())) for t,v in zip(vocab,projection)])
        db.executemany("INSERT INTO passages VALUES (?,?,?,?,?)", [(*r,json.dumps(normalize(v.tolist()))) for r,v in zip(rows,matrix @ projection)])


@dataclass
class Hit:
    id: str
    source: str
    text: str
    cosine: float
    bm25: float
    score: float


class Index:
    def __init__(self, strategy="paragraph"):
        with sqlite3.connect((ROOT / f"{strategy}.sqlite").as_uri()+"?mode=ro", uri=True) as db:
            self.model = {t:(idf,json.loads(v)) for t,idf,v in db.execute("SELECT * FROM model")}
            self.rows = [(i,s,t,json.loads(v),Counter(tokens(t))) for i,s,_,t,v in db.execute("SELECT * FROM passages ORDER BY id")]
        self.mean = sum(c.total() for *_,c in self.rows)/len(self.rows)
        self.df = Counter(t for *_,c in self.rows for t in c)

    def search(self, question, method="hybrid", source=None, k=4):
        terms = Counter(tokens(question))
        size = len(next(iter(self.model.values()))[1])
        projection = [0.0]*size
        for term,count in terms.items():
            if term in self.model:
                idf,v = self.model[term]
                for j,component in enumerate(v):
                    projection[j] += component*(1+math.log(count))*idf
        query = normalize(projection)
        hits = []
        for i,s,text,v,c in self.rows:
            if source and s != source:
                continue
            b = 0.0
            for t in terms.keys() & c.keys():
                idf = math.log(1+(len(self.rows)-self.df[t]+0.5)/(self.df[t]+0.5))
                b += idf*c[t]*2.2/(c[t]+1.2*(0.25+0.75*c.total()/self.mean))
            hits.append(Hit(i,s,text,dot(query,v),b,0))
        highest = max((h.bm25 for h in hits), default=0)
        for h in hits:
            if method=="semantic":
                h.score = h.cosine
            elif method=="bm25":
                h.score = h.bm25
            else:
                h.score = 0.6*max(0,h.cosine)+0.4*(h.bm25/highest if highest else 0)
        return sorted(hits,key=lambda h:(-round(h.score,10),h.id))[:k]


if __name__=="__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--build", action="store_true")
    args = parser.parse_args()
    if args.build:
        for strategy in ["paragraph","fixed"]:
            build(strategy)
            print(strategy, len(Index(strategy).rows), "chunks")
