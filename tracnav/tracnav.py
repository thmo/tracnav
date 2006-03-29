# -*- coding: utf-8 -*-
"""
= !TracNav: The Navigation Bar for Trac =

This macro implements a fully customizable navigation bar for the Trac
wiki engine. The contents of the navigation bar is a wiki page itself
and can be edited like any other wiki page through the web
interface. The navigation bar supports hierarchical ordering of
topics. The design of !TracNav mimics the design of the !TracGuideToc
that was originally supplied with Trac. The drawback of !TracGuideToc
is that it is not customizable without editing its source code and
that it does not support hierarchical ordering.

== Installation ==

See http://projects.edgewall.com/trac/wiki/TracPlugins.

== Usage ==

To use !TracNav, create an index page for your site and call the
TracNav macro on each page, where the navigation bar should be
displayed. The index page is a regular wiki page. The page with the
table of contents must include an unordered list of links that should
be displayed in the navigation bar.

To display the navigation bar on a page, you must call the !TracNav
macro on that page an pass the name of your table of contents as
argument.

== Additional information and a life example ==

Please visit: http://svn.ipd.uka.de/trac/javaparty/wiki/TracNav.

== Author and License ==

Copyright 2005, 2006
 *  Bernhard Haumacher (haui at haumacher.de)
 *  Thomas Moschny (moschny at ipd.uni-karlsruhe.de)

{{{
This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
}}}

"""
__id__        = '$Id$'
__version__   = '3.92pre1'
__revision__  = '$LastChangedRevision$'

import re
from trac.core import Component, implements
from trac.wiki.api import WikiSystem, IWikiMacroProvider
from trac.web.chrome import ITemplateProvider, add_stylesheet
from trac.wiki.model import WikiPage
from trac.wiki.formatter import Formatter, OneLinerFormatter
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO


TRACNAVHOME = "http://svn.ipd.uka.de/trac/javaparty/wiki/TracNav"
LISTRULE = re.compile(r"^(?P<indent>[ \t\v]+)\* +(?P<rest>.*)$", re.M)
ALLOWED_MACROS = ["image"]


class TocFormatter(OneLinerFormatter):
    """
    Basically the OneLinerFormatter, but additionally remembers the
    last wiki link.
    """
    def format_toc(self, wikitext):
        self.link = None
        out = StringIO()
        OneLinerFormatter.format(self, wikitext, out)
        return out.getvalue(), self.link

    def __init__(self, env, req = None):
        OneLinerFormatter.__init__(self, env)
        # OneLinerFormatter sets req to None
        self.req = req
        self.link = None

    def _make_link(self, namespace, target, match, label):
        if namespace == 'wiki':
            self.link = target
        return OneLinerFormatter._make_link(
            self, namespace, target, match, label)

    def _macro_formatter(self, match, fullmatch):
        name = fullmatch.group('macroname').lower()
        if name == 'br':
            return ' '
        elif name in ALLOWED_MACROS:
            # leapfrog the OneLinerFormatter
            return Formatter._macro_formatter(self, match, fullmatch)
        else:
            return ''

    # FIXME: what about _make_relative_link() ?
    # FIXME: CamelCase links are special and not handled by the Formatter...


class TracNav(Component):

    implements(IWikiMacroProvider, ITemplateProvider)

    def get_toc(self, req, name):
        """
        Fetch the wiki page containing the toc, if available.
        """
        preview = req.args.get('preview', '')
        curpage = req.args.get('page')

        if preview and name == curpage:
            return req.args.get('text', '')
        elif WikiSystem(self.env).has_page(name):
            return WikiPage(self.env, name).text
        else:
            return ''


    def get_toc_entry(self, toc_text, req):
        """
        Parse and format the entries in toc_text.
        """
        formatter = TocFormatter(self.env, req)
        for match in LISTRULE.finditer(toc_text):
            indent = len(match.group('indent'))
            label, link = formatter.format_toc(match.group('rest'))
            yield indent, link, label


    def get_toc_entry_and_indent(self, gen):
        """
        Filter for get_toc_entry().  The first call to next() returns the
        indentation level of the next entry (or -1 if there are no more
        entries) and the second call returns the entry itself.
        """
        while True:
            try:
                indent, link, label = gen.next()
            except StopIteration:
                yield -1
                return
            yield indent
            yield link, label        


    def _parse_toc(self, gen, next_indent, level = 0):
        """
        Construct the toc tree at the given level.
        """
        toclist = []
        if next_indent > level:
            sublist, next_indent = self._parse_toc(gen, next_indent, level + 1)
            if next_indent < level: # level is empty
                return sublist, next_indent
            else:                   # broken indentation structure
                toclist.append((None, None, sublist))
        while True:
            if next_indent == level:
                (link, label), next_indent = gen.next(), gen.next()
                if next_indent > level:
                    sublist, next_indent = self._parse_toc(gen, next_indent, level + 1)
                    toclist.append((link, label, sublist))
                else:
                    toclist.append((link, label, None))
            else:
                assert next_indent < level
                return toclist, next_indent


    def parse_toc(self, toc_text, req = None):
        """
        Recursively construct the toc tree using _parse_toc().
        """
        gen = self.get_toc_entry(toc_text, req)
        gen = self.get_toc_entry_and_indent(gen)
        toc, _ = self._parse_toc(gen, gen.next())
        return toc


    def execute(self, req, args):
        """
        Main routine of the wiki macro.
        """

        #init
        out = StringIO()
        names = []
        collapse = True
        curpage = req.args.get('page','')

        # parse arguments
        if args:
            for arg in args.split('|'):
                if arg == 'nocollapse':
                    collapse = False
                else:
                    names.append(arg)
        
        # header
        col = 0
        out.write('%s<div class="wiki-toc trac-nav">\n' % self.i(col))
        col += 1
        out.write('%s<h2><a href="%s">TracNav</a> menu</h2>\n' % \
                  (self.i(col), TRACNAVHOME))

        # add TOCs
        for name in (names or ["TOC"]):
            toc_text = self.get_toc(req, name)
            toc = self.parse_toc(toc_text, req)
            if not toc:
                toc = self.parse_toc(' * TOC "%s" is empty!' % name)
            if collapse:
                (found, filtered) = self.filter_toc(curpage, toc)
                if found:
                    self.display_all(out, req, name, filtered, col)
            else:
                self.display_all(out, req, name, toc, col)

        # footer 
        col -= 1
        out.write('%s</div>\n' % self.i(col))

        # add our stylesheet
        add_stylesheet(req, 'tracnav/css/tracnav.css')

        # emit 
        return out.getvalue()


    def filter_toc(self, curpage, toc, level = 0):
        found = 0
        result = []
        for name, title, sub in toc:
            if sub == None:
                if name == curpage:
                    found = 1
                result.append((name, title, None))
            else:
                (subfound, subtoc) = self.filter_toc(curpage, sub, level + 1)
                if subfound:
                    found = 1
                if subfound or (name == None):
                    if level == 0 and name != None:
                        prepended = [(name, title, subtoc)]
                        prepended.extend(result)
                        result = prepended
                    else:
                        result.append((name, title, subtoc))
                else:
                    result.append((name, title, []))
        return (found, result)


    def i(self, col):
        return ' ' * col


    def display_all(self, out, req, name, toc, col):
        preview = req.hdf.getValue('args.preview', '')
        curpage = req.hdf.getValue('wiki.page_name', '')

        if (not preview) and req.hdf.getValue('trac.acl.WIKI_MODIFY', ''):
            out.write('%s<div class="edit"><a href="%s?edit=yes">edit</a></div>\n' % \
                    (self.i(col), self.env.href.wiki(name)))
        out.write('%s<ul>\n' % self.i(col))
        col += 1
        self.display(out, curpage, toc, 0, col)
        col -= 1
        out.write('%s</ul>\n' % self.i(col))


    def display(self, out, curpage, toc, depth, col):
        for name, title, sub in toc:
            li_style = ' style="padding-left: %dem;"' % (depth + 1)
            if sub == None:
                if name == curpage:
                    cls = ' class="active"'
                else:
                    cls = ''
                out.write('%s<li%s%s>%s</li>\n' % \
                        (self.i(col), li_style, cls, title))
            else:
                out.write('%s<li%s>\n' % (self.i(col), li_style))
                col += 1
                if name == None or sub:
                    out.write('%s<h4>%s</h4>\n' % (self.i(col), title))
                else:
                    out.write('%s<h4>%s...</h4>\n' % (self.i(col), title))
                col -= 1
                out.write('%s</li>\n' % self.i(col))
                if len(sub) > 0:
                    self.display(out, curpage, sub, depth + 1, col)


    def get_macros(self):
        yield 'TracNav'


    def render_macro(self, req, name, args):
        return self.execute(req, args)
    

    def get_macro_description(self, name):
        from inspect import getdoc, getmodule
        return getdoc(getmodule(self))


    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('tracnav', resource_filename(__name__, 'htdocs'))]


    def get_templates_dirs(self):
        # we don't provide templates
        return []
    
