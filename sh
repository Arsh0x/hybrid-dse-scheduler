import itertools
import string

# Pattern: S H _ _ _ R I
characters = string.ascii_lowercase

for middle in itertools.product(characters, repeat=3):
    name = "sh" + "".join(middle) + "ri"
    print(name)
