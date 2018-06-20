#!/usr/bin/env python3
import sys
import json
import os
import os.path
from string import Template

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

htmlTemplate = Template("""<!DOCTYPE html>
<html lang="en" xml:lang="en" xmlns="http://www.w3.org/1999/xhtml">
  <head>
    <meta charset="utf-8" />
    <title>${title}</title>
    <style>
article h1 {
font-size: 2em;
}
li[typeof="ScholarlyArticle"] {
margin-top:1em;
}
li[typeof="ScholarlyArticle"]:first-child,
li[typeof="ScholarlyArticle"] dl {
margin-top:0;
}
li[typeof="ScholarlyArticle"] dt:first-child {
display:none;
}
section[typeof="PublicationIssue"] dt,
section[typeof="PublicationIssue"] dd,
li[typeof="ScholarlyArticle"] dt,
li[typeof="ScholarlyArticle"] dd {
display:inline;
}
section[typeof="PublicationIssue"] dt:after,
li[typeof="ScholarlyArticle"] dt:after {
content:": ";
}
section[typeof="PublicationIssue"] dd,
li[typeof="ScholarlyArticle"] dd {
margin:0;
}
section[typeof="PublicationIssue"] dd + dt:before,
li[typeof="ScholarlyArticle"] dd + dt:before {
content:"\\A";
white-space:pre;
}
    </style>
  </head>
  <body vocab="http://schema.org/">
    <header>
      <p>This is a web copy of <a property="mainEntityOfPage http://purl.org/pav/derivedFrom http://www.w3.org/ns/prov#wasDerivedFrom" href="${src}"><span property="name">${title}</span></a>. Published in WWW2018 Proceedings © 2018 International World Wide Web Conference Committee, published under <a rel="license" property="license" href="https://creativecommons.org/licenses/by/4.0/"> Creative Commons CC By 4.0 License</a>.</p>
      <p>The <a property="http://purl.org/pav/createdWith" typeof="SoftwareSourceCode" href="https://github.com/usable-oa/thewebconf2018/tree/master/scripts">modifications</a> from the originals are solely to improve HTML aiming to make them <a href="https://doi.org/10.1038/sdata.2016.18" property="publishingPrinciples">Findable, Accessible, Interoperable and Reusable</a>, augmenting metadata and (just in case) avoiding ACM trademarks. To help improve this, please <a property="discussionUrl" href="https://github.com/usable-oa/thewebconf2018/issues">raise an issue or pull request</a>.</p>
      <p>To cite these papers, use their DOI. To link to or reference their HTML version here, use the corresponding w3id.org permalinks.</p>
    </header>
    <main>
      <article about="" typeof="Article">
        <h1 property="name">${title}</h1>
${toc}
${parts}
      </article>
    </main>
  </body>
</html>
""")




def crossref(crossref):
    with open(crossref, encoding="utf-8") as f:
        j = json.load(f)
    if not j["status"] == "ok":
        print("Error in CrossRef JSON, did API call fail?", file=sys.stderr)
        return 1
    doc = j["message"]
    return {
        "path": crossref,
        "doi": find_doi(doc),
        "authors": find_authors(doc),
        "year": find_year(doc),
        "title": find_title(doc),
        "proceeding": find_proceeding(doc)
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
    return escape_html(", ".join(auths))

def find_year(doc):
    return doc["issued"]["date-parts"][0][0]

def find_title(doc):
    t = doc["title"][0]
    # TODO: Check [1] and "subtitle" ?
    return escape_html(t)

articleTemplate = Template(
"""              <li resource="${permalink}" id="${doi}" typeof="ScholarlyArticle">
                <a href="${permalink}"><span property="name">${title}</span></a>
                <dl>
                  <dt>Authors</dt>
                  <dd xml:lang="" lang="">${authors}</dd>
                  <dt>DOI</dt>
                  <dd><a href="https://doi.org/${doi}" property="sameAs">${doi}</a></dd>
                  <dt>Permalink</dt>
                  <dd><a href="${permalink}">${permalink}</a></dd>
                </dl>
              </li>""")

def listing_html(crossref):
    return articleTemplate.substitute(**crossref)


def escape_html(t):
    """HTML-escape the text in `t`."""
    return (t
        .replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        .replace("'", "&#39;").replace('"', "&quot;")
        )

def find_crossrefs(folder):
    for root, dirs, files in os.walk(folder):
        if "crossref.json" in files:
            yield os.path.join(root, "crossref.json")

issueTemplate = Template(
"""        <section id="${isbn}" resource="${uri}" typeof="PublicationIssue">
          <h2 property="name">${title}</h2>
          <dl>
            <dt>ISBN</dt> <dd lang="" property="isbn" xml:lang="">${isbn}</dd>
            <dt>Published</dt> <dd><time datatype="xsd:gYear" property="schema:datePublished">${year}</time></dd>
          </dl>
          <div datatype="rdf:HTML" property="schema:description">
            <ul rel="hasPart">
${articles}
            </ul>
          </div>
        </section>""")

# https://tools.ietf.org/html/rfc3187
PROCEEDINGS = [
    # Add here if you get a KeyError
    ("Proceedings of the 2018 World Wide Web Conference on World Wide Web  - WWW '18", "9781450356398"),
    ("Companion of the The Web Conference 2018 on The Web Conference 2018  - WWW '18", "9781450356404"),
]
ISBN = dict(PROCEEDINGS)


def isbn(proceeding_title, asUri=False):
    i = ISBN[proceeding_title].replace("-", "")
    if asUri:    
        return "urn:isbn:" + i
    else:
        return i

def proceeding(articles):
    # We'll pick proceeding title from the first article
    first = articles[0]

    i = {    
        "title": first["proceeding"],
        "year": first["year"],
        "isbn": isbn(first["proceeding"]),
        "uri": isbn(first["proceeding"], asUri=True),
        "articles": "\n".join(map(listing_html, articles))
    }
    return issueTemplate.substitute(**i)

def anchors():
    a = []
    # Fixed order
    for title,isbn in PROCEEDINGS:
        a.append('            <li><a href="#%s">%s</a></li>' % (isbn, title))

    return Template(
"""        <nav>
          <ul>
$li
          </ul>
        </nav>""").substitute(li="\n".join(a))

def main(folder="../doi/", permalink=None):
    # TODO: 
    # 1. Loop over folder to run crossref()
    # 2. Group by proceedings
    # 3. Sort by DOI
    # 4. substitute using htmlTemplate and escape_html    
    proceedings = {}

    first = None
    for c in map(crossref, find_crossrefs(folder)):
        if first is None:
            first = c

        if permalink:
            c["permalink"] = permalink + c["doi"]
        else:
            c["permalink"] = os.path.dirname(c["path"])
        k = c["proceeding"]
        if k not in proceedings:
            proceedings[k] = []
        proceedings[k].append(c)
    
    if not first:
        print("Found no crossref.json files within " + folder, file=sys.stderr)
        return 1

    for p in proceedings.values():
       p.sort(key=lambda v : v["doi"])

    parts = []
    # Fixed order
    for p,isdn in PROCEEDINGS:
        parts.append(proceeding(proceedings[p]))

    # Pick proceeding title from first one
    v = {
        "title": "Proceedings of the 2018 World Wide Web Conference",
        # TODO: Avoid hardcoded
        "src": "https://www2018.thewebconf.org/proceedings/",
        "toc": anchors(),
        "parts": "\n\n".join(parts)
    }

    print(htmlTemplate.substitute(**v))

if __name__ == "__main__":
    if "-h" in sys.argv:
        help()
        sys.exit(0)
    i = main(*sys.argv[1:])
    sys.exit(i)
