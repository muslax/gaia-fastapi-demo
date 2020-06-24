import os

PROJECT_NAME = os.getenv("PROJECT_NAME", "Gaia Behavioral API")

API_V1_STR = "/api/v1"

SECRET_KEY = "PATIKANJI"
# ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 1  # 60 minutes * 24 hours * 1 day = 1 day
ACCESS_TOKEN_EXPIRE_MINUTES = 60 # 2 minutes

SERVER_NAME = os.getenv("SERVER_NAME")
SERVER_HOST = os.getenv("SERVER_HOST")

# SENTRY_DSN              = "https://7c0ba73507f748718b791fe973177be4@sentry.io/3481918"
SENTRY_DSN = os.getenv("SENTRY_DSN")

BACKEND_CORS_ORIGINS = "http://localhost, http://localhost:8000"

MAX_CONNECTIONS_COUNT = int(os.getenv("MAX_CONNECTIONS_COUNT", 100))
MIN_CONNECTIONS_COUNT = int(os.getenv("MIN_CONNECTIONS_COUNT", 10))

MONGODB_URI = os.getenv("MONGODB_URI")
MONGODB_NAME = os.getenv("MONGODB_NAME")

DOCTYPE_TEST            = "tests"
DOCTYPE_USER            = "users"
DOCTYPE_PERSONA         = "personas"
DOCTYPE_COMPANY         = "companies"
DOCTYPE_PROJECT         = "projects"
DOCTYPE_EV_CSI          = "ev_csi"
DOCTYPE_EV_GATE         = "ev_gate"
DOCTYPE_EV_MATE         = "ev_mate"
DOCTYPE_EV_GPQ          = "ev_gpq"
DOCTYPE_EV_SJT          = "ev_sjt"

COMPANY_SYMBOL_LENGTH   = 6
USERNAME_MIN_LENGTH     = 5
USERNAME_MAX_LENGTH     = 10
DATA_PAGING_DEFAULT     = 20

SMTP_TLS                = True
SMTP_PORT               = 587

SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
EMAILS_FROM_EMAIL = os.getenv("EMAILS_FROM_EMAIL")

EMAILS_FROM_NAME        = PROJECT_NAME
EMAIL_RESET_TOKEN_EXPIRE_HOURS = 48
EMAIL_TEMPLATES_DIR     = "./app/email-templates/build"
EMAILS_ENABLED          = SMTP_HOST and SMTP_PORT and EMAILS_FROM_EMAIL

USERTYPE_GAIA           = "gaia"
USERTYPE_LICENSE        = "license"
USERTYPE_CLIENT         = "client"
USERTYPE_EXPERT         = "expert"
USERTYPE_PERSONA        = "persona"

ROLE_SUPERUSER          = "superuser"
ROLE_LICENSE_PUBLISHER  = "license-publisher"
ROLE_PROJECT_CREATOR    = "project-creator"
ROLE_PROJECT_MANAGER    = "project-manager"
ROLE_PROJECT_MEMBER     = "project-member"

GPQ_TOTAL_ITEMS         = 120


# FIRST_SUPERUSER = os.getenv("FIRST_SUPERUSER")
# FIRST_SUPERUSER_PASSWORD = os.getenv("FIRST_SUPERUSER_PASSWORD")

# USERS_OPEN_REGISTRATION = getenv_boolean("USERS_OPEN_REGISTRATION")

EMAIL_TEST_USER = "you@me.com"
