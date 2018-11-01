# CONFIGURATION for "CarPhaS.py"


# Input files:
ROOT = "../../"  # path to "MZ" and "PA" directories
SHERDS_DIR = ROOT + "MZ/A/CERAMICS/exogen/strata/"  # all files are read, all listed sherds are processed
LEXICA_FILE = "../Pantry/UGR_lexica.txt"  # lexica abbreviations
MZA_LEXICA_FILE = ROOT + "MZ/A/MZ/TEXTS/A2/mza-lexicon.txt"  # 'phase' names

TEMPLATE_INDEX = "./template_index.htm"  # file for formatting data in HTML
TEMPLATE_STRATA = "./template_strata.htm"


# Output files:
OUT_INDEX = ROOT + "MZ/A/CERAMICS/TEXTS/C2/index.htm"
OUT_INDEX_VESSEL = ROOT + "MZ/A/CERAMICS/TEXTS/C2/index_vessel.htm"
OUT_STRATA_DIR = ROOT + "MZ/A/CERAMICS/TEXTS/C2/strata/"  # output: an HTML page for each data (e.g. sherds, phase, ..)
OUT_DATABASE = ROOT + "MZ/A/CERAMICS/TEXTS/C2/database/spreadsheet.txt"


# Output error messages:
LOG = "./CerPhaS.log"
ERRORS_DIRECTORY = ROOT + "MZ/A/CERAMICS/-   non-canonical/to be checked - CerPhaS/"
NOT_PARSED_FILE = ERRORS_DIRECTORY + "not-parsed.txt"
NOT_FOUND_FILE = ERRORS_DIRECTORY + "not-found.txt"
NO_SHAPE_FILE = ERRORS_DIRECTORY + "no-shape.txt"
