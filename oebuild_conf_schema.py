
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

OPENERP_TYPE = {
"type": "object",
"properties": {
    URL: {"type": "string", "format": "uri"},
    BZR_REV: {"type": "string", "pattern": "^[0-9]+$", "required": False},
}
}
DEPENDENCY_TYPE = {
    "type": "object",
    "properties": {
        SCM: {"type": "string", "enum": (SCM_GIT, SCM_BZR)},
        URL: {"type": "string", "format": "uri"},
        GIT_BRANCH: {"type": "string"},
        DESTINATION: {"type": "string", "format": "uri"},
        ADDONS_PATH: {"type": "string", "format": "uri", "required": False},
    }
}
OEBUILD_SCHEMA = {
    "type": "object",
    "properties": {
        OEBUILD_VERSION: {"type": "string", "pattern": "^[0-9]+|.[0-9]+$"},
        "openerp-server": OPENERP_TYPE,
        "openerp-addons": OPENERP_TYPE,
        "openerp-web": OPENERP_TYPE,
        DEPENDENCIES: {
            "type": "array",
            "items": DEPENDENCY_TYPE
        }
    }
}