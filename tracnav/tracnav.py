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

 * Copyright 2005-2006, Bernhard Haumacher (haui at haumacher.de)
 * Copyright 2005-2007, Thomas Moschny (moschny at ipd.uni-karlsruhe.de)

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
__revision__  = '$LastChangedRevision$'

import re
from trac.core import Component, implements
from trac.wiki.api import WikiSystem, IWikiMacroProvider
from trac.web.chrome import ITemplateProvider, add_stylesheet
from trac.wiki.model import WikiPage
from trac.wiki.formatter import Formatter, OneLinerFormatter
from StringIO import StringIO


TRACNAVHOME = "http://svn.ipd.uka.de/trac/javaparty/wiki/TracNav"
LISTRULE = re.compile(r"^(?P<indent>[ \t\v]+)\* +(?P<rest>.*)$", re.M)
ALLOWED_MACROS = ["image"]


class TocFormatter(OneLinerFormatter):
    """
    Basically the OneLinerFormatter, but additionally remembers the
    last wiki link.
    """
    def __init__(self, context):
        OneLinerFormatter.__init__(self, context)
        self.lastlink = None

    def format_toc(self, wikitext):
        self.lastlink = None
        out = StringIO()
        OneLinerFormatter.format(self, wikitext, out)
        return out.getvalue(), self.lastlink

    def _make_link(self, namespace, target, match, label):
        if namespace == 'wiki':
            self.lastlink = target
        return OneLinerFormatter._make_link(
            self, namespace, target, match, label)

    def _macro_formatter(self, match, fullmatch):
        name = fullmatch.group('macroname').lower()
        if name in ALLOWED_MACROS:
            # leapfrog the OneLinerFormatter
            return Formatter._macro_formatter(self, match, fullmatch)
        else:
            # use the OneLinerFormatter
            return OneLinerFormatter._macro_formatter(self, match, fullmatch)

    # FIXME: what about _make_relative_link() ?
    # FIXME: CamelCase links are special and not handled by the Formatter...


class Invocation(object):

    def __init__(self, formatter, args, out):

        # save for later use
        self.formatter = formatter

        # shortcuts
        self.env = formatter.env
        self.req = formatter.req

        # output
        self.out = out
        self.col = 0
        
        # needed several times
        self.preview = self.req.args.get('preview', '')
        self.curpage = self.req.args.get('page', 'WikiStart')
        self.modify = self.req.perm.has_permission('WIKI_MODIFY')

        # parse arguments
        self.names = []
        self.collapse = True
        if args:
            for arg in args.split('|'):
                if arg == 'nocollapse':
                    self.collapse = False
                else:
                    self.names.append(arg)

    def get_toc(self, name):
        """
        Fetch the wiki page containing the toc, if available.
        """
        if self.preview and name == self.curpage:
            return self.req.args.get('text', '')
        elif WikiSystem(self.env).has_page(name):
            return WikiPage(self.env, name).text
        else:
            return ''

    def get_toc_entry(self, toc_text):
        """
        Parse and format the entries in toc_text.
        """
        formatter = TocFormatter(self.formatter.context)
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

    def parse_toc(self, toc_text):
        """
        Recursively construct the toc tree using _parse_toc().
        """
        gen = self.get_toc_entry_and_indent(self.get_toc_entry(toc_text))
        toc, _ = self._parse_toc(gen, gen.next())
        return toc

    def write(self, what):
        self.out.write(' ' * self.col)
        self.out.write(what)
        return self

    def indent_more(self):
        self.col += 1
        return self

    def indent_less(self):
        self.col -= 1
        return self

    def run(self):
        """
        Main routine of the wiki macro.
        """
        # header
        self.write('<div class="wiki-toc trac-nav">\n').indent_more()
        self.write('<h2><a href="%s">TracNav</a> menu</h2>\n' % TRACNAVHOME)

        # add TOCs
        for name in (self.names or ["TOC"]):
            toc = self.parse_toc(self.get_toc(name))
            if not toc:
                toc = self.parse_toc(' * TOC "%s" is empty!' % name)
            found, filtered = self.filter_toc(toc)
            if (not self.collapse) or (not found):
                self.display_all(name, toc)
            else:
                self.display_all(name, filtered)

        # footer
        self.indent_less().write('</div>\n')

        # add our stylesheet
        add_stylesheet(self.req, 'tracnav/css/tracnav.css')

    def filter_toc(self, toc, level = 0):
        found = False
        result = []
        for name, title, sub in toc:
            if sub == None:
                if name == self.curpage:
                    found = True
                result.append((name, title, None))
            else:
                subfound, subtoc = self.filter_toc(sub, level + 1)
                if subfound:
                    found = True
                if subfound or (name == None):
                    if level == 0 and name != None:
                        prepended = [(name, title, subtoc)]
                        prepended.extend(result)
                        result = prepended
                    else:
                        result.append((name, title, subtoc))
                else:
                    result.append((name, title, []))
        return found, result

    def display_all(self, name, toc):
        if (not self.preview) and (self.modify):
            self.write('<div class="edit"><a href="%s?action=edit">edit</a></div>\n' % \
                self.req.href.wiki(name))
        self.write('<ul>\n').indent_more()
        self.display(toc, 0)
        self.indent_less().write('</ul>\n')

    def display(self, toc, depth):
        for name, title, sub in toc:
            li_style = ' style="padding-left: %dem;"' % (depth + 1)
            if sub == None:
                if name == self.curpage:
                    cls = ' class="active"'
                else:
                    cls = ''
                self.write('<li%s%s>%s</li>\n' % (li_style, cls, title))
            else:
                self.write('<li%s>\n' % li_style).indent_more()
                if name == None or sub:
                    self.write('<h4>%s</h4>\n' % title)
                else:
                    self.write('<h4>%s...</h4>\n' % title)
                self.indent_less().write('</li>\n')
                if len(sub) > 0:
                    self.display(sub, depth + 1)


class TracNav(Component):

    implements(IWikiMacroProvider, ITemplateProvider)

    def get_macros(self):
        yield 'TracNav'
        yield 'JPNav' # legacy

    def render_macro(self, formatter, name, args):
        out = StringIO()
        Invocation(formatter, args, out).run()
        return out.getvalue()

    def get_macro_description(self, name):
        from inspect import getdoc, getmodule
        return getdoc(getmodule(self))

    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('tracnav', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        # we don't provide templates
        return []
