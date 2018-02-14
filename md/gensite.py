#!/usr/bin/env python3
# -*- mode: python; coding: utf-8; -*-
"""Site generation script.  Requires mdplay (https://github.com/thomas-hori/mdplay ).

Written by HarJIT in 2017, 2018.

This software is provided 'as-is', without any express or implied warranty. In no
event will the authors be held liable for any damages arising from the use of this
software.

Permission is granted to anyone to use this software for any purpose, including
commercial applications, and to alter it and redistribute it freely, subject to
the following restrictions:

    1. The origin of this software must not be misrepresented; you must not
       claim that you wrote the original software. If you use this software in
       a product, an acknowledgment in the product documentation would be 
       appreciated but is not required.

    2. Altered source versions must be plainly marked as such, and must not be 
       misrepresented as being the original software.

    3. This notice may not be removed or altered from any source distribution.

"""
import sys, os, subprocess, glob, xml.dom.minidom, smartypants

blumming_mode = smartypants.Attr.w | smartypants.Attr.u | smartypants.Attr.q
smartypants.tags_to_skip.extend(["blockquote", "title"])

save_wd = os.getcwd()
os.chdir(os.path.dirname(os.path.abspath(sys.argv[0])))
sys.path.append(os.path.abspath("../../mdplay"))

import mdplay, mdplay.writers.html, mdplay.writers._writehtml

tag = """<!-- Global site tag (gtag.js) - Google Analytics -->
<script async src="https://www.googletagmanager.com/gtag/js?id=UA-114124215-1"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());

  gtag('config', 'UA-114124215-1');
</script>"""

def gen_linkitem(document, url, title, tag="li", clas=None):
    b = document.createElement(tag)
    c = b
    if url:
        c = document.createElement("a")
        c.setAttribute("href", url)
        b.appendChild(c)
    if clas:
        b.setAttribute("class", clas)
    c.appendChild(document.createTextNode(title))
    return b

def gen_link(document, url, title):
    c = document.createElement("a")
    c.setAttribute("href", url)
    c.appendChild(document.createTextNode(title))
    return c

def gen_nav(document, root = ""):
    for item in sorted(list(glob.glob("." + root + "/*.md")) + list(glob.glob("." + root + "/*.txt"))):
        base_name = os.path.basename(os.path.splitext(item)[0])
        if base_name.startswith("__") and base_name.endswith("__"):
            continue # Special-use files such as __footer__.txt
        title = open(item, "rU", encoding="utf-8").readline().split("-=-")
        title = title[1] if len(title) > 2 else base_name
        yield gen_linkitem(document, "/" + base_name + ".html", title)
    for item in sorted(list(glob.glob("." + root + "/*-external"))):
        data = open(item, "rU").read().strip()
        url, title = data.split(" ", 1)
        yield gen_linkitem(document, url, title, clas="externalmenulink")
    for item in sorted(list(glob.glob("."+root+"/*"))):
        if os.path.isdir(item):
            nf = os.path.join(item,"__name__")
            if os.path.exists(nf):
                mynav = gen_linkitem(document, None, open(nf,"rU").read())
            else:
                mynav = gen_linkitem(document, None, os.path.basename(item.rstrip("/")))
            mynav2 = document.createElement("ul")
            mynav.appendChild(mynav2)
            for i in gen_nav(document, root + "/" + item):
                mynav2.appendChild(i)
            yield mynav

footertemplate = open("__footer__.txt", "rU", encoding="utf-8").read()
sitename = open("__sitename__", "rU", encoding="utf-8").read()

for item in list(glob.glob("./*.md"))+list(glob.glob("./*/*.md"))+list(glob.glob("./*.txt"))+list(glob.glob("./*/*.txt")):
    base_name = os.path.split(os.path.splitext(item)[0])[-1]
    title = open(item, "rU").readline().split("-=-")
    title = title[1] if len(title)>2 else base_name
    f = open(item, "rU")
    tree = list(mdplay.parse_file(f, ["extradirective", "noverifyurl"]))
    mdi = xml.dom.minidom.getDOMImplementation()
    # <!doctype...> and <html...>
    document = mdi.createDocument("http://www.w3.org/1999/xhtml", "html", mdi.createDocumentType("html", None, None))
    document.documentElement.setAttribute("xmlns", "http://www.w3.org/1999/xhtml")
    document.documentElement.setAttribute("lang", "en")
    #document.documentElement.setAttribute("xml:lang", "en")
    # <head>
    head = document.createElement("head")
    document.documentElement.appendChild(head)
    # <meta charset...> (stick this first in the head)
    charset = document.createElement("meta")
    charset.setAttribute("charset", "UTF-8")
    head.appendChild(charset)
    # viewport size (for mobile browsers)
    charset = document.createElement("meta")
    charset.setAttribute("name", "viewport")
    charset.setAttribute("content", "width=320,initial-scale=1")
    head.appendChild(charset)
    # <title>
    titlebar = document.createElement("title")
    head.appendChild(titlebar)
    titlebar.appendChild(document.createTextNode(title.strip() + " - " + sitename.strip()))
    # X-UA-Compatible
    xua = document.createElement("meta")
    xua.setAttribute("http-equiv", "X-UA-Compatible")
    xua.setAttribute("content", "IE=Edge")
    head.appendChild(xua)
    # <link rel="stylesheet"...>
    stylesheet = document.createElement("link")
    stylesheet.setAttribute("rel", "stylesheet")
    stylesheet.setAttribute("type", "text/css")
    stylesheet.setAttribute("href", "css/site.css")
    head.appendChild(stylesheet)
    # <body>
    body = document.createElement("body")
    document.documentElement.appendChild(body)
    # column-content
    col2 = document.createElement("div")
    col2.setAttribute("id", "column-content")
    body.appendChild(col2)
    for domn in mdplay.writers.html.html_out_part(tree, document, flags=["insecuredirective", "html5"], mode="xhtml"):
        col2.appendChild(domn)
    blum1 = mdplay.writers._writehtml.tohtml(document, "utf-8", mode="xhtml")
    blum2 = smartypants.smartypants(blum1.decode("utf-8"), blumming_mode)
    blum4 = mdplay.writers.html._escape(blum2.replace("</title>", "</title>" + tag), 1, "xhtml")
    open("../"+base_name+".html", "w", encoding="ascii", errors="xmlcharrefreplace").write(blum4)

os.chdir("..")
try:
    subprocess.call(["git","add","*.html"])
    subprocess.call(["git","add","*/*.html"])
    subprocess.call(["git","add","posters/*.pdf"])
    subprocess.call(["git","add","-u"])
    subprocess.call(["git","commit","-m","automated commit"])
    subprocess.call(["git","push","origin","gh-pages"])
finally:
    os.chdir(save_wd)

