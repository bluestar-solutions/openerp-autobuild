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
NAME = "name"
PUBLIC = "public"
PRIVATE = "private"

OPENERP_TYPE = {
    "type": "object",
    "properties": {
        URL: {"type": "string", "format": "uri", "required": False},
        BZR_REV: {"type": "string", "pattern": "^[0-9]+$", "required": False},
    }
}
DEPENDENCY = {
    "type": "object",
    "properties": {
        NAME: {"type": "string", "required": True},
        DESTINATION: {"type": "string", "format": "uri", "required": False},
        ADDONS_PATH: {"type": "string", "format": "uri", "required": False},
        PUBLIC: {
            "type": "object", 
            "oneOf": [
                {"$ref": "#/definitions/gitDependency"}, 
                {"$ref": "#/definitions/bzrDependency"}
            ], 
            "required": True
        },
        PRIVATE: {
            "type": "object", 
            "oneOf": [
                {"$ref": "#/definitions/gitDependency"}, 
                {"$ref": "#/definitions/bzrDependency"}
            ], 
            "required": False
        },
    }
}
OEBUILD_SCHEMA = {
    "type": "object",
    "properties": {
        OEBUILD_VERSION: {"type": "string", "pattern": "^[0-9]+|.[0-9]+$", "required": True},
        PROJECT: {"type": "string", "pattern": "^[a-z|0-9|-]+$", "required": True},
        "openerp-server": OPENERP_TYPE,
        "openerp-addons": OPENERP_TYPE,
        "openerp-web": OPENERP_TYPE,
        DEPENDENCIES: {
            "type": "array",
            "items": {"type": DEPENDENCY},
            "required": True
        }
    },
    "definitions": {
        "gitDependency": {
            "type": "object",
            "properties": {
                SCM: {"type": "string", "pattern": SCM_GIT, "required": True},
                URL: {"type": "string", "format": "uri", "required": True},
                GIT_BRANCH: {"type": "string", "required": False},
            },
        },
        "bzrDependency": {
            "type": "object",
            "properties": {
                SCM: {"type": "string", "pattern": SCM_BZR, "required": True},
                URL: {"type": "string", "format": "uri", "required": True},
                BZR_REV: {"type": "string", "pattern": "^[0-9]+$", "required": False},
            },
        }        
    }
}