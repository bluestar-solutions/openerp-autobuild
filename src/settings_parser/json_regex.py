# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP Autobuild
#    Copyright (C) 2012-2013 Bluestar Solutions Sàrl (<http://www.blues2.ch>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import json

update_version = lambda v_from, v_to: (r'("oebuild-version"\s*:\s*)"%s"' % v_from, r'\1"%s"' % v_to)

remove_param = lambda p_name: (r'"%s"\s*:\s*".*"\s*,?\s*\n?' % p_name, r'')
add_param_before = lambda p_name, p_value, before_p_name: (r'(\n?)(\s*)("%s"\s*:)' % (before_p_name), r'\n\2"%s": "%s"\n\2\3' % (p_name, p_value))
set_param_value = lambda p_name, p_value: (r'("%s"\s*:\s*)(".*")' % (p_name), r'\1"%s"' % (p_value))
set_param_array = lambda p_name, p_array: (r'("%s"\s*:\s*)(\[.*\])' % (p_name), r'\1%s' % (json.dumps(p_array)))
remove_param_array = lambda p_name: (r'(,?\s*)?"%s"\s*:\s*\{\s*.*\s*\}' % p_name, r'')
