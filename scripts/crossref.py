#!/usr/bin/env python3
import sys
import json

def help():
    print("""crossref.py [crossref] [permalink] [-d]")

Extract authorship and title from crossref JSON

If parameter [crossref] is supplied. it is assumed to be a file path
to a JSON file from the crossref API.

If the parameter is missing or -, the JSON is read from stdin.

Output on stdout is schema.org-annotated HTML5+RDFa that can be included 
in the top of the corresponding article HTML.

If the parameter [permalink] is provided, it will be assumed to be
a hyperlink to the HTML article (as part of a listing). 
In this case the output will also include additional 
information such as DOI and proceedings.

If the parameter -d is provided, the parsed JSON is output with 
pretty-printing instead of the HTML.

""")

def main(crossref=None, permalink=None, debug=False, *args):
    if crossref is None or crossref == "-":
        # Always read JSON as UTF-8 even if system encoding differs
        f = TextIOWrapper(sys.stdin, encoding="utf-8")
    else:
        f = open(crossref, encoding="utf-8")
    j = json.load(f)
    if not j["status"] == "ok":
        print("Error in CrossRef JSON, did API call fail?", file=sys.stderr)
        return 1
    doc = j["message"]

    doi = find_doi(doc)
    authors = find_authors(doc)
    year = find_year(doc)
    title = escape_html(find_title(doc))

    if "-d" in args or permalink == "-d":
        json.dump(j, sys.stdout, sort_keys=True, indent=2)
    elif permalink:
        listing_html(doi, title, authors, year, permalink, find_proceeding(doc))
    else:
        embed_html(doi, title, authors, year)
    return 0

def find_doi(doc):
    return doc["DOI"]

def find_proceeding(doc):
    # TODO: What if there isn't any?
    return doc["container-title"][0]

def find_authors(doc):
    auths = []
    for a in doc["author"]:
        # FIXME: Should be name order agnostic
        auths.append("%s %s" % (a["given"], a["family"]))
    return auths

def find_year(doc):
    return doc["issued"]["date-parts"][0][0]

def find_title(doc):
    t = doc["title"][0]
    # TODO: Check [1] and "subtitle" ?
    return t

def listing_html(doi, title, authors, year, permalink, proceeding):
    print("""  <li about="https://doi.org/%s" id="%s" typeof="ScholarlyArticle">
    <a href="doi/%s/" property="name" rel="sameAs">%s</a>
    <dl>
      <dt>Authors</dt>
      <dd xml:lang="" lang="">%s</dd>
      <dt>Issue</dt>
      <dd property="isPartOf" typeof="PublicationIssue"><em property="name">%s</em></dd>
      <dt>DOI</dt>
      <dd><a href="https://doi.org/%s">%s</a></dd>
      <dt>Permalink</dt>
      <dd><a href="%s" property="sameAs">%s</a></dd>
    </dl>
  </li>""" % (doi, doi, doi, title, ", ".join(authors), proceeding, doi, doi, permalink, permalink))

def embed_html(doi, title, authors, year):
    print("""<li about="https://doi.org/%s" id="%s" typeof="ScholarlyArticle">
    <a href="doi/%s/" property="name" rel="sameAs">%s</a>

    <dl>
      <dt>Authors</dt>
      <dd xml:lang="" lang="">%s</dd>
    </dl>
  </li>""" % (doi, doi, doi, ", ".join(authors)))


def escape_html(t):
    """HTML-escape the text in `t`."""
    return (t
        .replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        .replace("'", "&#39;").replace('"', "&quot;")
        )

if __name__ == "__main__":
    if "-h" in sys.argv:
        help()
        sys.exit(0)
    try:
        i = main(*sys.argv[1:])
        if i:
            print(sys.argv, file=sys.stderr)
    except Exception as e:
        print(sys.argv, file=sys.stderr)
        raise e
    sys.exit(i)
