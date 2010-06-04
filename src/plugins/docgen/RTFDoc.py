#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2000-2006  Donald N. Allingham
# Copyright (C) 2007-2009  Brian G. Matherly
# Copyright (C) 2009       Gary Burton
# Copyright (C) 2010       Peter Landgren
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#

# $Id:RTFDoc.py 9912 2008-01-22 09:17:46Z acraphae $

#------------------------------------------------------------------------
#
# python modules
#
#------------------------------------------------------------------------
from gen.ggettext import gettext as _

#------------------------------------------------------------------------
#
# Load the base BaseDoc class
#
#------------------------------------------------------------------------
from gui.utils import open_file_with_default_application
from gen.plug.docgen import (BaseDoc, TextDoc, FONT_SERIF, PARA_ALIGN_RIGHT,
                             PARA_ALIGN_CENTER, PARA_ALIGN_JUSTIFY)
import ImgManip
import Errors
import Utils

#------------------------------------------------------------------------
#
# RTF uses a unit called "twips" for its measurements. According to the 
# RTF specification, 1 point is 20 twips. This routines converts 
# centimeters to twips
#
# 2.54 cm/inch 72pts/inch, 20twips/pt
#
#------------------------------------------------------------------------
def twips(cm):
    return int(((cm/2.54)*72)+0.5)*20

#------------------------------------------------------------------------
#
# Rich Text Format Document interface. The current interface does not
# use style sheets. Instead it writes raw formatting.
#
#------------------------------------------------------------------------
class RTFDoc(BaseDoc,TextDoc):

    #--------------------------------------------------------------------
    #
    # Opens the file, and writes the header. Builds the color and font
    # tables.  Fonts are chosen using the MS TrueType fonts, since it
    # is assumed that if you are generating RTF, you are probably 
    # targeting Word.  This generator assumes a Western Europe character
    # set.
    #
    #--------------------------------------------------------------------
    def open(self,filename):
        if filename[-4:] != ".rtf":
            self.filename = filename + ".rtf"
        else:
            self.filename = filename

        try:
            self.f = open(self.filename,"w")
        except IOError,msg:
            errmsg = "%s\n%s" % (_("Could not create %s") % self.filename, msg)
            raise Errors.ReportError(errmsg)
        except:
            raise Errors.ReportError(_("Could not create %s") % self.filename)
        
        style_sheet = self.get_style_sheet()

        self.f.write(
            '{\\rtf1\\ansi\\ansicpg1252\\deff0\n'
            '{\\fonttbl\n'
            '{\\f0\\froman\\fcharset0\\fprq0 Times New Roman;}\n'
            '{\\f1\\fswiss\\fcharset0\\fprq0 Arial;}}\n'
            '{\colortbl\n'
            )

        self.color_map = {}
        index = 1
        self.color_map[(0,0,0)] = 0
        self.f.write('\\red0\\green0\\blue0;')
        for style_name in style_sheet.get_paragraph_style_names():
            style = style_sheet.get_paragraph_style(style_name)
            fgcolor = style.get_font().get_color()
            bgcolor = style.get_background_color()
            if fgcolor not in self.color_map:
                self.color_map[fgcolor] = index
                self.f.write('\\red%d\\green%d\\blue%d;' % fgcolor)
                index += 1
            if bgcolor not in self.color_map:
                self.f.write('\\red%d\\green%d\\blue%d;' % bgcolor)
                self.color_map[bgcolor] = index
                index += 1
        self.f.write('}\n')
        self.f.write(
            '\\kerning0\\cf0\\viewkind1' +
            '\\paperw%d' % twips(self.paper.get_size().get_width()) +
            '\\paperh%d' % twips(self.paper.get_size().get_height()) +
            '\\margl%d' % twips(self.paper.get_left_margin()) +
            '\\margr%d' % twips(self.paper.get_right_margin()) +
            '\\margt%d' % twips(self.paper.get_top_margin()) +
            '\\margb%d' % twips(self.paper.get_bottom_margin()) +
            '\\widowctl\n'
            )
        self.in_table = 0
        self.text = ""

    #--------------------------------------------------------------------
    #
    # Write the closing brace, and close the file.
    #
    #--------------------------------------------------------------------
    def close(self):
        self.f.write('}\n')
        self.f.close()

        if self.open_req:
            open_file_with_default_application(self.filename)

    #--------------------------------------------------------------------
    #
    # Force a section page break
    #
    #--------------------------------------------------------------------
    def end_page(self):
        self.f.write('\\sbkpage\n')

    #--------------------------------------------------------------------
    #
    # Starts a paragraph. Instead of using a style sheet, generate the
    # the style for each paragraph on the fly. Not the ideal, but it 
    # does work.
    #
    #--------------------------------------------------------------------
    def start_paragraph(self,style_name,leader=None):
        self.opened = 0
        style_sheet = self.get_style_sheet()
        p = style_sheet.get_paragraph_style(style_name)

        # build font information

        f = p.get_font()
        size = f.get_size()*2
        bgindex = self.color_map[p.get_background_color()]
        fgindex = self.color_map[f.get_color()]
        if f.get_type_face() == FONT_SERIF:
            self.font_type = '\\f0'
        else:
            self.font_type = '\\f1'
        self.font_type += '\\fs%d\\cf%d\\cb%d' % (size,fgindex,bgindex)

        if f.get_bold():
            self.font_type += "\\b"
        if f.get_underline():
            self.font_type += "\\ul"
        if f.get_italic():
            self.font_type += "\\i"

        # build paragraph information

        if not self.in_table:
            self.f.write('\\pard')
        if p.get_alignment() == PARA_ALIGN_RIGHT:
            self.f.write('\\qr')
        elif p.get_alignment() == PARA_ALIGN_CENTER:
            self.f.write('\\qc')
        self.f.write(
            '\\ri%d' % twips(p.get_right_margin()) +
            '\\li%d' % twips(p.get_left_margin()) +
            '\\fi%d' % twips(p.get_first_indent())
            )
        if p.get_alignment() == PARA_ALIGN_JUSTIFY:
            self.f.write('\\qj')
        if p.get_padding():
            self.f.write('\\sa%d' % twips(p.get_padding()/2.0))
        if p.get_top_border():
            self.f.write('\\brdrt\\brdrs')
        if p.get_bottom_border():
            self.f.write('\\brdrb\\brdrs')
        if p.get_left_border():
            self.f.write('\\brdrl\\brdrs')
        if p.get_right_border():
            self.f.write('\\brdrr\\brdrs')
        if p.get_first_indent():
            self.f.write('\\fi%d' % twips(p.get_first_indent()))
        if p.get_left_margin():
            self.f.write('\\li%d' % twips(p.get_left_margin()))
        if p.get_right_margin():
            self.f.write('\\ri%d' % twips(p.get_right_margin()))

        if leader:
            self.opened = 1
            self.f.write('\\tx%d' % twips(p.get_left_margin()))
            self.f.write('{%s ' % self.font_type)
            self.write_text(leader)
            self.f.write(self.text)
            self.text = ""
            self.f.write('\\tab}')
            self.opened = 0
    
    #--------------------------------------------------------------------
    #
    # Ends a paragraph. Care has to be taken to make sure that the 
    # braces are closed properly. The self.opened flag is used to indicate
    # if braces are currently open. If the last write was the end of 
    # a bold-faced phrase, braces may already be closed.
    #
    #--------------------------------------------------------------------
    def end_paragraph(self):
        if not self.in_table:
            self.f.write(self.text)
            if self.opened:
                self.f.write('}')
                self.opened = 0
            self.f.write('\n\\par')
            self.text = ""
        else:
            if self.text == "":
                self.write_text(" ")
            self.text += '}'

    #--------------------------------------------------------------------
    #
    # Inserts a manual page break
    #
    #--------------------------------------------------------------------
    def page_break(self):
        self.f.write('\\page\n')

    #--------------------------------------------------------------------
    #
    # Starts boldfaced text, enclosed the braces
    #
    #--------------------------------------------------------------------
    def start_bold(self):
        if self.opened:
            self.f.write('}')
        self.f.write('{%s\\b ' % self.font_type)
        self.opened = 1

    #--------------------------------------------------------------------
    #
    # Ends boldfaced text, closing the braces
    #
    #--------------------------------------------------------------------
    def end_bold(self):
        self.opened = 0
        self.f.write(self.text)
        self.text = ""
        self.f.write('}')

    def start_superscript(self):
        self.text += '{{\*\updnprop5801}\up10 '

    def end_superscript(self):
        self.text += '}'

    #--------------------------------------------------------------------
    #
    # Start a table. Grab the table style, and store it. Keep a flag to
    # indicate that we are in a table. This helps us deal with paragraphs
    # internal to a table. RTF does not require anything to start a 
    # table, since a table is treated as a bunch of rows.
    #
    #--------------------------------------------------------------------
    def start_table(self, name,style_name):
        self.in_table = 1
        styles = self.get_style_sheet()
        self.tbl_style = styles.get_table_style(style_name)

    #--------------------------------------------------------------------
    #
    # End a table. Turn off the table flag
    #
    #--------------------------------------------------------------------
    def end_table(self):
        self.in_table = 0

    #--------------------------------------------------------------------
    #
    # Start a row. RTF uses the \trowd to start a row. RTF also specifies
    # all the cell data after it has specified the cell definitions for
    # the row. Therefore it is necessary to keep a list of cell contents
    # that is to be written after all the cells are defined.
    #
    #--------------------------------------------------------------------
    def start_row(self):
        self.contents = []
        self.cell = 0
        self.prev = 0
        self.cell_percent = 0.0
        self.f.write('\\trowd\n')

    #--------------------------------------------------------------------
    #
    # End a row. Write the cell contents, separated by the \cell marker,
    # then terminate the row
    #
    #--------------------------------------------------------------------
    def end_row(self):
        self.f.write('{')
        for line in self.contents:
            self.f.write(line)
            self.f.write('\\cell ')
        self.f.write('}\\pard\\intbl\\row\n')

    #--------------------------------------------------------------------
    #
    # Start a cell. Dump out the cell specifics, such as borders. Cell
    # widths are kind of interesting. RTF doesn't specify how wide a cell
    # is, but rather where it's right edge is in relationship to the 
    # left margin. This means that each cell is the cumlative of the 
    # previous cells plus its own width.
    #
    #--------------------------------------------------------------------
    def start_cell(self,style_name,span=1):
        styles = self.get_style_sheet()
        s = styles.get_cell_style(style_name)
        self.remain = span -1
        if s.get_top_border():
            self.f.write('\\clbrdrt\\brdrs\\brdrw10\n')
        if s.get_bottom_border():
            self.f.write('\\clbrdrb\\brdrs\\brdrw10\n')
        if s.get_left_border():
            self.f.write('\\clbrdrl\\brdrs\\brdrw10\n')
        if s.get_right_border():
            self.f.write('\\clbrdrr\\brdrs\\brdrw10\n')
        table_width = float(self.paper.get_usable_width())
        for cell in range(self.cell,self.cell+span):
            self.cell_percent += float(self.tbl_style.get_column_width(cell))
        cell_width = twips((table_width * self.cell_percent)/100.0)
        self.f.write('\\cellx%d\\pard\intbl\n' % cell_width)
        self.cell += 1

    #--------------------------------------------------------------------
    #
    # End a cell. Save the current text in the content lists, since data
    # must be saved until all cells are defined.
    #
    #--------------------------------------------------------------------
    def end_cell(self):
        self.contents.append(self.text)
        self.text = ""

    #--------------------------------------------------------------------
    #
    # Add a photo. Embed the photo in the document. Use the Python 
    # imaging library to load and scale the photo. The image is converted
    # to JPEG, since it is smaller, and supported by RTF. The data is
    # dumped as a string of HEX numbers.
    #
    #--------------------------------------------------------------------
    def add_media_object(self, name, pos, x_cm, y_cm, alt=''):

        nx, ny = ImgManip.image_size(name)

        if (nx, ny) == (0,0):
            return

        if (nx, ny) == (0,0):
            return

        ratio = float(x_cm)*float(ny)/(float(y_cm)*float(nx))

        if ratio < 1:
            act_width = x_cm
            act_height = y_cm*ratio
        else:
            act_height = y_cm
            act_width = x_cm/ratio

        buf = ImgManip.resize_to_jpeg_buffer(name, int(act_width*40), 
                                             int(act_height*40))

        act_width = twips(act_width)
        act_height = twips(act_height)

        self.f.write('{\*\shppict{\\pict\\jpegblip')
        self.f.write('\\picwgoal%d\\pichgoal%d\n' % (act_width,act_height))
        index = 1
        for i in buf:
            self.f.write('%02x' % ord(i))
            if index%32==0:
                self.f.write('\n')
            index = index+1
        self.f.write('}}\\par\n')
    
    def write_styled_note(self, styledtext, format, style_name,
                          contains_html=False):
        """
        Convenience function to write a styledtext to the latex doc. 
        styledtext : assumed a StyledText object to write
        format : = 0 : Flowed, = 1 : Preformatted
        style_name : name of the style to use for default presentation
        contains_html: bool, the backend should not check if html is present. 
            If contains_html=True, then the textdoc is free to handle that in 
            some way. Eg, a textdoc could remove all tags, or could make sure
            a link is clickable. RTFDoc prints the html without handling it
        """
        text = str(styledtext)
        if format:
            # Preformatted note
            for line in text.split('\n'):
                self.start_paragraph(style_name)
                self.write_text(line)
                if self.in_table:
                #    # Add LF when in table as in indiv_complete report
                    self.write_text('\n')
                self.end_paragraph()
        else:
            firstline = True
            for line in text.split('\n\n'):
                self.start_paragraph(style_name)
                if len(line) > 0:
                    # Remember first char, can be a LF.
                    firstchar = line[0] 
                    # Replace all LF's with space and reformat.
                    line = line.replace('\n',' ')
                    line = ' '.join(line.split())
                    # If remembered first char is LF, insert in front of lines
                    #This takes care of the case with even number of empty lines.
                    if firstchar == '\n':
                        line = firstchar + line
                    #Insert LF's if not first line.
                    if not firstline:
                        line = '\n\n' + line
                else:
                    # If odd number of empty lines line will be empty.
                    line = '\n\n'
                self.write_text(line)
                self.end_paragraph()
                firstline = False
            self.start_paragraph(style_name)
            self.write_text('\n')
            self.end_paragraph()

    def write_endnotes_ref(self,text,style_name):
        """
        Overwrite base method for lines of endnotes references
        """
        for line in text.split('\n'):
            self.start_paragraph(style_name)
            self.write_text(line)
            if self.in_table:
                # Add LF when in table as in indiv_complete report
                self.write_text('\n')
            self.end_paragraph()
        # Write an empty para after all ref lines for each source
        self.start_paragraph(style_name)
        self.end_paragraph()

    #--------------------------------------------------------------------
    #
    # Writes text. If braces are not currently open, open them. Loop 
    # character by character (terribly inefficient, but it works). If a
    # character is 8 bit (>127), convert it to a hex representation in 
    # the form of \`XX. Make sure to escape braces.
    #
    #--------------------------------------------------------------------
    def write_text(self,text,mark=None):
    # Convert to unicode, just in case it's not. Fix of bug 2449.
        text = unicode(text)
        text = text.replace('\n','\n\\par ')
        if self.opened == 0:
            self.opened = 1
            self.text += '{%s ' % self.font_type

        for i in text:
            if ord(i) > 127:
                if ord(i) < 256:
                    self.text += '\\\'%2x' % ord(i)
                else:
                    # If (uni)code with more than 8 bits: 
                    # RTF req valus in decimal, not hex.
                    self.text += '\\uc1\\u%d\\uc0' % ord(i)
            elif i == '{' or i == '}' :
                self.text += '\\%s' % i
            else:
                self.text += i
