"""PubMed search handler -- NCBI E-utilities (pure Python, no R)."""
from __future__ import annotations
import argparse, csv, sys, time, urllib.request, urllib.parse, xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Optional
ESEARCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
EFETCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
def search_pubmed(query: str, max_results: int = 20) -> List[dict]:
    params = urllib.parse.urlencode({"db":"pubmed","term":query,"retmax":max_results,"retmode":"xml"})
    with urllib.request.urlopen(f"{ESEARCH}?{params}", timeout=30) as r:
        root = ET.fromstring(r.read())
    ids = [e.text for e in root.findall(".//Id") if e.text]
    if not ids: return []
    time.sleep(0.4)
    fetch_params = urllib.parse.urlencode({"db":"pubmed","id":",".join(ids),"retmode":"xml"})
    with urllib.request.urlopen(f"{EFETCH}?{fetch_params}", timeout=30) as r:
        fetch_root = ET.fromstring(r.read())
    results = []
    for article in fetch_root.findall(".//PubmedArticle"):
        title = article.findtext(".//ArticleTitle","")
        abstract = article.findtext(".//Abstract/AbstractText","")
        journal = article.findtext(".//Journal/Title","")
        year = article.findtext(".//PubDate/Year","")
        authors = [a.findtext("LastName","") for a in article.findall(".//Author") if a.findtext("LastName")]
        pmid = article.findtext(".//PMID","")
        doi = article.findtext(".//ArticleId[@IdType='doi']","")
        results.append({"Title":title,"Authors":"; ".join(authors[:5]),"Journal":journal,"Year":year,"Abstract":abstract[:500],"PMID":pmid,"DOI":doi})
    return results
def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="PubMed Search Handler")
    parser.add_argument("--query", required=True, help="Search query")
    parser.add_argument("--max-results", type=int, default=20)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args(argv)
    out = Path(args.output_dir); out.mkdir(parents=True, exist_ok=True)
    results = search_pubmed(args.query, args.max_results)
    csv_path = out / "pubmed_results.csv"
    if results:
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=["Title","Authors","Journal","Year","Abstract","PMID","DOI"])
            w.writeheader(); w.writerows(results)
    print(f"Found {len(results)} articles, saved to {csv_path}")
    return 0
if __name__ == "__main__": sys.exit(main())
