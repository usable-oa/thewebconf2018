#!/usr/bin/env python3
import sys
import json

def help():
    print("""makeindex.py [doi-folder] [permalink-base]")

Index a doi folder, output a HTML file.

The index will include light-weight schema.org annotations.

If [doi-folder] is given, it will be searched for the files "crossref.json".
Links will go to the neighbouring "index.html" 
(e.g. <a href="doi/10.1234/1231/index.html">..</a>)

If the [permalink-base] is provided, links will instead go 
to the permalinks generated by appending the DOI to the base URI,
e.g. https://w3id.org/oa/10.1234/1231

""")

htmlTemplate = """
<!DOCTYPE html>
<html lang="en" xml:lang="en" xmlns="http://www.w3.org/1999/xhtml">
  <head>
    <meta charset="utf-8" />
    <title>${title}</title>
  </head>
  <body vocab="http://schema.org/">
    <header>
      <p>This is a web copy of <a property="mainEntityOfPage http://purl.org/pav/derivedFrom http://www.w3.org/ns/prov#wasDerivedFrom" href=${src}><span property="name">${title}</span></a>.
 Published in WWW2018 Proceedings © 2018 International World Wide Web Conference Committee, published under
 <a rel="license" property="license" href="https://creativecommons.org/licenses/by/4.0/">
 Creative Commons CC By 4.0 License</a>.</p>
      <p>The <a property="http://purl.org/pav/createdWith" typeof="SoftwareSourceCode" href="https://github.com/usable-oa/thewebconf2018/tree/master/scripts">modifications</a> from the originals are solely to improve HTML aiming to make them <a href="https://doi.org/10.1038/sdata.2016.18" property="publishingPrinciples">Findable, Accessible, Interoperable and Reusable</a>, augmenting metadata and (just in case) avoiding ACM trademarks. To help improve this, please <a property="discussionUrl" href="https://github.com/usable-oa/thewebconf2018/issues">raise an issue or pull request</a>.</p>
      <p>To cite these papers, use their DOI. To link to or reference their HTML version here, use the corresponding w3id.org permalinks.</p>
    </header>
    <main>
      <article about="" typeof="Article">
        <h1 property="name">${title}</h1>
        <div datatype="rdf:HTML" property="schema:description">
          <ul rel="hasPart">
            ${parts}
          </ul>
        </div>
      </article>
    </main>
  </body>
</html>
"""


def crossref(crossref=None, permalink=None, debug=False):
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
    return {
        "doi": find_doi(doc),
        "authors": find_authors(doc),
        "year": find_year(doc),
        "title": find_title(doc)
    }

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
    print("""  <li about="%s" id="%s" typeof="ScholarlyArticle">
    <a href="%s" property="name">%s</a>
    <dl>
      <dt>Authors</dt>
      <dd xml:lang="" lang="">%s</dd>
      <dt>DOI</dt>
      <dd><a href="https://doi.org/%s" property="sameAs">%s</a></dd>
      <dt>Permalink</dt>
      <dd><a href="%s">%s</a></dd>
    </dl>
  </li>""" % (permalink, doi, permalink, title, ", ".join(authors), doi, doi, permalink, permalink))


def escape_html(t):
    """HTML-escape the text in `t`."""
    return (t
        .replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        .replace("'", "&#39;").replace('"', "&quot;")
        )

def main(folder="./doi/", permalink=None):
    # TODO: 
    # 1. Loop over folder to run crossref()
    # 2. Group by proceedings
    # 3. Sort by DOI
    # 4. substitute using htmlTemplate and escape_html
    print(htmlTemplate)

if __name__ == "__main__":
    if "-h" in sys.argv:
        help()
        sys.exit(0)
    i = main(*sys.argv[1:])
    sys.exit(i)
