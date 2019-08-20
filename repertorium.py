"""
Script to parse the Notarial Repertorium. 
"""

import re
from collections import defaultdict

FILE = "data/repertorium.txt"

keys = {
    'benoeming': "",
    'admissie': "",
    'creatie': "",
    'aanstelling': "",
    'vermeld als notaris': "",
    'leeftijd bij aanstelling':
    "De vroegste datum van benoeming, aanstelling of admissie; ongeacht op nominatie van welke plaats de admissie heeft plaatsgevonden.",
    'aanstelling voor een ambachtsheerlijkheid': "",
    'vermeld als notaris van een ambachtsheerlijkheid': "",
    'notaris voor een instelling': "",
    'notaris voor een vorst': "",
    'protocol': "",
    'faillissement': "",
    'ambtsbeëindiging':
    "Deze werd soms veel later ingeschreven. De redenen om het notarisambt te beëindigen lopen uiteen van een andere functie, vertrek naar elders, slechte gezondheid, ouderdom, overlijden tot gekwiteerd (het ambt verlaten). Een aantal notarissen is, soms met zeer zware straffen, wegens overtredingen uit het ambt gezet.",
    'tijdelijk ambt gestaakt': "",
    'opvolger van': "",
    'opgevolgd door': "",
    'samenwerking met': "",
    'familierelatie': "",
    'adres':
    "Uit de ambtsperiode. Indien deze niet bekend is, zijn ook de daaraan voorafgaande of nakomende straatnamen opgenomen. De vier grote grachten zijn opgedeeld aan de hand van nadere adres aanduidingen. Het kantooradres heeft voorrang boven het huisadres. Achter de straatnaam is zo nodig tussen haakjes de huidige naam vermeld.",
    'godsdienst': "",
    'was klerk bij': "",
    'studie': "",
    'vreemde talen in zijn protocol': "",
    'vreemde talen welke hij kende': "",
    'zijn klerken waren': "",
    'nevenfuncties': "De andere functies tijdens zijn leven.",
    'herkomst': "",
    'geboren': "",
    'doop': "",
    'ondertrouw': "",
    'huwelijk': "",
    'gescheiden': "",
    'overlijden': "",
    'begraven': "",
    'familierelaties': "",
    'nevenfunctie': ""
}


def main():

    with open(FILE, encoding='utf-8') as infile:
        lines = infile.read().split('\n')

    ## Possible fieldnames
    # All fields that are filled in in the document. This list is taken from
    # page 26 in the original document. Added to the keys are variants of the
    # keys such as `familierelaties` (plural) and `nevenfunctie` (singular)
    # that are also used in the book.

    notary2page = getNotary2Page(lines)


def getNotary2Page(lines):

    notary2page = defaultdict(list)

    notaryNumber = None
    for line in lines:
        if '<pagina' in line:
            page = re.findall(r'pagina (\d+)', line)[0]

            # In case the notary is described on two pages
            if notaryNumber is not None:
                notary2page[notaryNumber].append(page)
        else:
            match = re.findall(r'^(\d+)\. ', line)
            if match != []:
                notaryNumber = int(match[0])

                notary2page[notaryNumber].append(page)

    return notary2page


if __name__ == "__main__":
    main()