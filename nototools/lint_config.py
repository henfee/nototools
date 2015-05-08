#!/usr/bin/python
#
# Copyright 2015 Google Inc. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Custom configuration of lint for font instances."""

# the structure is a list of conditions and tests.  a condition says when to apply
# the following test.  these are processed in order and are cumulative, and
# where there is a conflict the last instructions win.

# both conditions and tests can vary in specifity, a condition can for example simply
# indicate all fonts by a vendor, or indicate a particuar version of a particular font.

# At the end of the day, we have a particular font, and want to know which tests to
# run and which failures to ignore or report.  lint_config builds up a structure from
# a customization file that makes allows this api.

import re

class FontInfo(object):
  def __init__(self, filename, name, style, script, variant, weight, hinted, vendor, version):
    self.filename = filename
    self.name = name
    self.style = style
    self.script = script
    self.variant = variant
    self.weight = weight
    self.hinted = hinted
    self.vendor = vendor
    self.version = version

  def __repr__(self):
    return str(self.__dict__)


class FontCondition(object):

  def _init_fn_map():
    def test_lt(lhs, rhs):
      return float(lhs) < float(rhs)
    def test_le(lhs, rhs):
      return float(lhs) <= float(rhs)
    def test_eq(lhs, rhs):
      return float(lhs) == float(rhs)
    def test_ne(lhs, rhs):
      return float(lhs) != float(rhs)
    def test_ge(lhs, rhs):
      return float(lhs) >= float(rhs)
    def test_gt(lhs, rhs):
      return float(lhs) > float(rhs)
    def test_is(lhs, rhs):
      return lhs == rhs
    def test_in(lhs, rhs):
      return lhs in rhs
    def test_like(lhs, rhs):
      return rhs.match(lhs)

    return {
      '<': test_lt,
      '<=': test_le,
      '==': test_eq,
      '!=': test_ne,
      '>=': test_ge,
      '>': test_gt,
      'is': test_is,
      'in': test_in,
      'like': test_like
      }

  fn_map = _init_fn_map()


  def __init__(self, filename=None, name=None, style=None, script=None, variant=None, weight=None,
               hinted=None, vendor=None, version=None):
    """Each arg is either a string, or a pair of a fn of two args returning bool, and an object.
    When the arg is a pair, the target string is passed to the fn as the first arg and the
    second element of the pair is passed as the second arg."""

    self.filename = filename
    self.name = name
    self.style = style
    self.script = script
    self.variant = variant
    self.weight = weight
    self.hinted = hinted
    self.vendor = vendor
    self.version = version

  def modify(self, condition_name, fn_name, value):
    if not condition_name in self.__dict__:
      raise ValueError('FontCondition does not recognize: %s' % condition_name)

    if fn_name == '*':
      # no condition
      self.__dict__[condition_name] = None
      return

    if not value:
      # fn_name is value
      self.__dict__[condition_name] = fn_name
      return

    fn = self.fn_map[fn_name]
    if fn_name == 'in':
      value = set(value.split(','))
    elif fn_name == 'like':
      value = re.compile(value)
    self.__dict__[condition_name] = (fn, value)

  line_re = re.compile('([^ \t]+)\\s+([^ \t]+)(.*)?')
  def modify_line(self, line):
    line = line.strip()
    m = self.line_re.match(line)
    if not m:
      raise ValueError("FontCondition could not match '%s'" % line)
    condition_name = m.group(1)
    fn_name = m.group(2)
    value = m.group(3)
    if value:
      value = value.strip()
      if not value:
        value = None
    self.modify(condition_name, fn_name, value)

  def copy(self):
    return FontCondition(
        filename=self.filename, name=self.name, style=self.style, script=self.script,
        variant=self.variant, weight=self.weight, hinted=self.hinted, vendor=self.vendor,
        version=self.version)

  def accepts(self, fontinfo):
    for k in ['filename', 'name', 'style', 'script', 'variant', 'weight', 'hinted', 'vendor',
              'version']:
      test = getattr(self, k, None)
      if test:
        val = getattr(fontinfo, k, None)
        if isinstance(test, basestring):
          if test != val:
            return False
          continue
        if not test[0](val, test[1]):
          return False

    return True

  def __repr__(self):
    output = ['%s: %s' % (k,v) for k,v in self.__dict__.iteritems() if v]
    return 'FontCondition(%s)' % ', '.join(output)


class TestSpec(object):
  data = """
  name -- name table tests
    copyright
    family
    subfamily
    full_name
    version
      hinted_suffix
      match_head_table_version
      looks_like_number
    postscript
    trademark
    manufacturer
    vendor
    designer
    designer_url
    license
    license_url
  cmap -- cmap table tests
    tables
      missing
      unexpected
      format_12_has_bmp
      format_4_subset_of_12
    required
    script_required
    private_use
    non_chars
    disallowed -- ascii
  head -- head table tests
    hhea
      ascent
      descent
      linegap
    vhea
      linegap
    os2
      fstype
      ascender
      descender
      linegap
      winascent
      windescent
      achvendid
      weight_name
      weight_class
      fsselection
      unicoderange
  bounds -- glyf limits etc
    glyph
      ui_ymax
      ui_ymin
      ymax
      ymin
    font
      ui_ymax
      ui_ymin
      ymax
      ymin
  paths -- outline tests
    extrema -- on-curve extrema
    duplicate -- duplicate points
  gdef -- gdef tests
    glyphclassdef
      not_present -- table is missing but there are mark glyphs
      unlisted -- mark glyph is present and expected to be listed
      combining_unlisted -- mark glyph is combining but not listed as combining
      not_combining -- mark glyph is not combining but listed as combining
    attachlist
      duplicates
      out_of_order
    ligcaretlist
      not_present -- table is missing but there are ligatures
      not_ligature -- listed but not a ligature
      unlisted -- is a ligature but no caret
  complex -- gpos and gsub tests
    gpos
      missing
    gsub
      missing
  bidi -- tests bidi pairs, properties
    rtlm -- rtlm GSUB feature applied to non-private-use or non-mirrored character
    pair -- 'ompl' mirrored pair not in cmap but original is
    non_ompl -- non-ompl bidi char does not have rtml GSUB feature
  hmtx
    expected -- checks for expected advance relationships in whitespace, dashes
  glyf -- ogham?
    left_joiner -- non-zero lsb
    right_joiner -- rsb not -70
  reachable
  """

  def _process_data(data):
    """data is a hierarchy of tags. any level down to root can be enabled or disabled.  this
    builds a representation of the tag hierarchy from the text description."""
    tag_list = []
    indent = (0, '', None)
    for line in data.splitlines():
      if not line:
        continue
      ix = line.find('--')
      if ix != -1:
        comment = line[:ix+2].strip()
        line = line[:ix].rstrip()
      else:
        comment = ''
      line_indent = 0
      for i in range(len(line)):
        if line[i] != ' ':
          line_indent = i
          break
      line = line.strip()
      while line_indent <= indent[0]:
        if indent[2]:
          indent = indent[2]
        else:
          break
      tag = indent[1]
      if tag:
        tag += '/' + line
      else:
        tag = line
      tag_list.append((tag, comment))
      if line_indent > indent[0]:
        indent = (line_indent, tag, indent)
    return tag_list

  tags = _process_data(data)
  tag_set = frozenset([tag for tag,_ in tags])

  def __init__(self):
    self.touched_tags = set()
    self.enabled_tags = set()

  def _get_tag_set(self, tag):
    result = set()
    if not tag in self.tag_set:
      raise ValueError('unknown tag: %s' % tag)
    for candidate in self.tag_set:
      if candidate.startswith(tag):
        result.add(candidate)
    return result

  def enable(self, tag):
    tags = self._get_tag_set(tag)
    self.touched_tags |= tags
    self.enabled_tags |= tags

  def disable(self, tag):
    tags = self._get_tag_set(tag)
    self.touched_tags |= tags
    self.enabled_tags -= tags

  def apply(self, result):
    result -= self.touched_tags
    result |= self.enabled_tags

  line_rx = re.compile(r'\s*(enable|disable)\s*([a-z/]+).*')
  def modify_line(self, line):
    m = self.line_rx.match(line)
    if not m:
      raise ValueError('TestSpec could not parse ' + line)
    if m.group(1) == 'enable':
      self.enable(m.group(2))
    else:
      self.disable(m.group(2))

  def copy(self):
    result = TestSpec()
    result.touched_tags |= self.touched_tags
    result.enabled_tags |= self.enabled_tags
    return result

  def __repr__(self):
    enable_list = []
    disable_list = []
    for tag in self.touched_tags:
      if tag in self.enabled_tags:
        enable_list.append(tag)
      else:
        disable_list.append(tag)
    output = []
    if enable_list:
      output.append('enable:')
      output.extend(sorted(enable_list))
    if disable_list:
      output.append('disable:')
      output.extend(sorted(disable_list))
    return '\n'.join(output)

class SpecList(object):

  def __init__(self):
    self.specs = []

  def add_spec(self, font_condition, test_spec):
    self.specs.append((font_condition, test_spec))

  def get_test_set(self, font_info):
    result = set()
    result |= TestSpec.tag_set
    for spec in self.specs:
      if spec[0].accepts(font_info):
        spec[1].apply(result)
    return frozenset(result)

  def __repr__(self):
    return 'spec:\n' + '\nspec:\n'.join(str(spec) for spec in self.specs)


def parse_spec(spec):
  spec_list = SpecList()
  cur_condition = FontCondition()
  cur_test_spec = TestSpec()
  have_test = False
  for line in spec.splitlines():
    ix = line.find('#')
    if ix > -1:
      line = line[:ix]
    line = line.strip()
    if not line:
      continue
    if line == 'condition':
      if have_test:
        spec_list.add_spec(cur_condition.copy(), cur_test_spec)
        cur_test_spec = TestSpec()
        have_test = False
      cur_condition = FontCondition()
    elif line.startswith('enable') or line.startswith('disable'):
      cur_test_spec.modify_line(line)
      have_test = True
    else:
      if have_test:
        spec_list.add_spec(cur_condition.copy(), cur_test_spec)
        cur_test_spec = TestSpec()
        have_test = False
      cur_condition.modify_line(line)
  if have_test:
    spec_list.add_spec(cur_condition, cur_test_spec)

  return spec_list


def parse_spec_file(filename):
  with open(filename) as f:
    return parse_spec(f.read())

def main():
  test_spec="""
  # this is a test
  vendor Monotype
  disable paths/extrema # they prefer not to handle this
  filename NotoSans-Regular.ttf
  version 1.02
  enable paths/extrema # we agreed this was ok for this font and version

  condition
  filename NotoSansCJK-Regular.ttc
  disable name # no name tests for CJK regular"""

  print 'test spec:'
  print test_spec
  spec_list = parse_spec(test_spec)
  font_infos = [
    FontInfo('NotoSans-Regular.ttf', 'Noto', 'Sans', 'LGC', '', 'Regular', True,
             'Monotype', '1.02'),
    FontInfo('NotoSans-Regular.ttf', 'Noto', 'Sans', 'LGC', '', 'Regular', True,
             'Monotype', '1.03'),
    FontInfo('NotoSans-Bold.ttf', 'Noto', 'Sans', 'LGC', '', 'Regular', True,
             'Monotype', '1.02'),
    FontInfo('NotoSansCJK-Regular.ttc', 'Noto', 'Sans', 'CJK', '', 'Regular', True,
             'Adobe', '1.000')
    ]
  for fi in font_infos:
    print fi
    tests =  spec_list.get_test_set(fi)
    for test in ['paths/extrema', 'name/copyright']:
      print 'run test %s: %s' % (test, 'yes' if test in tests else 'no')

if __name__ == '__main__':
    main()
