"""Functions for filtering to a set of languages specified by cli flags."""

from absl import flags

FLAGS = flags.FLAGS

flags.DEFINE_list("filter_languages", None,
                  "List of language tags to filter the input data by.")

flags.DEFINE_string(
    "script_category", None, "One of 'latin', 'cjk', or 'arabic_indic'. "
    "Automatically configures filter_languages to "
    "the set of language tags for that script category.")

SCRIPT_CATEGORIES = {
    "latin": {
        "en",
        "vi",
        "es",
        "ru",
        "pt-PT",
        "fr",
        "id",
        "tr",
        "th",
        "pl",
        "de",
        "it",
        "nl",
        "cs",
        "sk",
        "da",
        "el",
        "sv",
        "sr",
        "fi",
        "ro",
        "hu",
        "no",
        "fil",
        "bg",
        "hr",
        "uk",
        "iw",
        "ms",
        "lt",
        "sl",
        "la",
        "az",
        "lv",
        "mk",
        "is",
        "ka",
        "et",
    },
    "arabic_indic":
    {"ar", "hi", "fa", "ml", "bn", "ta", "km", "te", "mr", "my", "ur"},
    "cjk": {"ja", "zh", "ko", "zh-Hant"},
}


def should_keep(lang):
  return not language_filter() or lang in language_filter()


def language_filter():
  """Returns the set of languages to filter sequences against.

  The filter set is based on the 'script_category' and 'filter_languages'
  flags. If 'script_category' is set it takes precedence.
  """
  if FLAGS.script_category:
    if FLAGS.script_category in SCRIPT_CATEGORIES:
      return SCRIPT_CATEGORIES[FLAGS.script_category]
    return set()

  if FLAGS.filter_languages:
    return set(FLAGS.filter_languages)

  return set()
