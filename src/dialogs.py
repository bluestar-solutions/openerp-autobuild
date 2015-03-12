# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP Autobuild
#    Copyright (C) 2013 Bluestar Solutions Sàrl (<http://www.blues2.ch>).
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

import sys

ANSWER_YES = "yes"
ANSWER_NO = "no"

VALID_ENTRIES = {
    "yes": ANSWER_YES,
    "y": ANSWER_YES,
    "ye": ANSWER_YES,
    "no": ANSWER_NO,
    "n": ANSWER_NO
}


def query_yes_no(question, default=ANSWER_YES):

    if default is None:
        prompt = " [y/n] "
    elif default == ANSWER_YES:
        prompt = " [Y/n] "
    elif default == ANSWER_NO:
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    while 1:
        sys.stdout.write(question + prompt)
        choice = raw_input().lower()
        if default is not None and choice == '':
            return default
        elif choice in VALID_ENTRIES.keys():
            return VALID_ENTRIES[choice]
        else:
            sys.stdout.write("Please respond with 'yes' or 'no' "
                             "(or 'y' or 'n').\n")

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
