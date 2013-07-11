
DEPENDENCIES = "dependencies"
SCM = "scm"
SCM_GIT = "git"
SCM_BZR = "bzr"
URL = "url"
BZR_REV = "bzr-rev"
GIT_BRANCH = "git-branch"
DESTINATION = "destination"
OEBUILD_VERSION = "oebuild-version"
ADDONS_PATH = "addons-path"
PROJECT = "project"

OPENERP_TYPE = {
"type": "object",
"properties": {
    URL: {"type": "string", "format": "uri"},
    BZR_REV: {"type": "string", "pattern": "^[0-9]+$", "required": False},
}
}
DEPENDENCY_GIT = {
    "type": "object",
    "properties": {
        SCM: {"type": "string", "pattern": SCM_GIT},
        URL: {"type": "string", "format": "uri"},
        GIT_BRANCH: {"type": "string", "required": True},
        DESTINATION: {"type": "string", "format": "uri"},
        ADDONS_PATH: {"type": "string", "format": "uri", "required": False},
    },
}
DEPENDENCY_BZR = {
    "type": "object",
    "properties": {
        SCM: {"type": "string", "pattern": SCM_BZR},
        URL: {"type": "string", "format": "uri"},
        BZR_REV: {"type": "string", "pattern": "^[0-9]+$", "required": True},
        DESTINATION: {"type": "string", "format": "uri"},
        ADDONS_PATH: {"type": "string", "format": "uri", "required": False},
    },
}
OEBUILD_SCHEMA = {
    "type": "object",
    "properties": {
        OEBUILD_VERSION: {"type": "string", "pattern": "^[0-9]+|.[0-9]+$", "required": True},
        PROJECT: {"type": "string", "pattern": "^[a-z|0-9|-]+$"},
        "openerp-server": OPENERP_TYPE,
        "openerp-addons": OPENERP_TYPE,
        "openerp-web": OPENERP_TYPE,
        DEPENDENCIES: {
            "type": "array",
            "items": {"type": [DEPENDENCY_GIT, DEPENDENCY_BZR]}
        }
    }
}