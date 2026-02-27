import gettext
import os

def setup_i18n(language: str):
    localedir = os.path.join(os.path.dirname(__file__), "locales")
    translation = gettext.translation(
        "messages",
        localedir=localedir,
        languages=[language],
        fallback=True
    )
    translation.install()
    return translation.gettext