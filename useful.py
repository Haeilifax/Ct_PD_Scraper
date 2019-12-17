numbers = [
    "zero", "one", "two", "three", "four", "five", "six", "seven"
    "eight", "nine", "ten", "eleven", "twelve", "thirteen", "fourteen"
    "fifteen", "sixteen", "seventeen", "eighteen", "nineteen", "twenty"
    ]
months = [
    "Jan.", "Feb.", "Mar.", "Apr.", "May.", "Jun.",
    "Jul.", "Aug.", "Sep.", "Oct.", "Nov.", "Dec."
    ]
states = [
    "A.L.", "A.K.", "A.Z.", "A.R.", "C.A.", "C.O.", "C.T.",
    "D.E.", "F.L.", "G.A.", "H.I.", "I.D.", "I.L.", "I.N.", "I.A.", "K.S.",
    "K.Y.", "L.A.", "M.E.", "M.D.", "M.A.", "M.I.", "M.N.", "M.S.", "M.O.",
    "M.T.", "N.E.", "N.V.", "N.H.", "N.J.", "N.M.", "N.Y.", "N.C.", "N.D.",
    "O.H.", "O.K.", "O.R.", "P.A.", "R.I.", "S.C.", "S.D.", "T.N.", "T.X.",
    "U.T.", "V.T.", "V.A.", "W.A.", "W.V.", "W.I.", "W.Y.",
    ]

def get_file_text(file_name):
    """Get text from file."""
    with open(file_name, "r") as f:
        text=f.read()
    return text

def clean_to_dict(dirty, delimeter="\n"):
    """Clean provided string and enter into dict.

    Cleans unparsed information based first on delimeter (default newline),
    then on colon space. Fills a dict with the cleaned information
    """
    clean_info = {}
    split_dirty = dirty.split(delimeter)
    for line in split_dirty:
        key_value = line.split(": ", 1)
        clean_info[key_value[0]] = key_value[1]
    return clean_info

# Cookie: PHPSESSID=58d7d9df41b849c3e695aab06e4630f6; wordpress_test_cookie=WP+Cookie+check; aiADB_PV=1