# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP Autobuild
#    Copyright (C) 2012-2015 Bluestar Solutions Sàrl (<http://www.blues2.ch>).
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
from shutil import copyfile


def update_from_2_1(params):
    copyfile(params.USER_CONFIG_FILE, params.USER_CONFIG_FILE + '.old')

    with open(params.USER_CONFIG_FILE, "r") as f:
        data = json.load(f)

    data['oebuild-version'] = "2.2"

    with open(params.USER_CONFIG_FILE, "w+") as f:
        f.write(json.dumps(data, indent=4))

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
