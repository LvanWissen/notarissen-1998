"""
Script to parse the Notarial Repertorium 1998. 
"""

import re
from collections import defaultdict

from datetime import datetime
import dateparser

FILE = "data/repertorium.txt"

## Cities

# Villages and cities that are mentioned. Notaries are categorized
# alphabetically and listed under the city they were working in. Sometimes, a
# reference is made to a previous mention in another city (e.g. `Zie: Mr. Paulus
#  van Beseler zie: Sloten`)

CITIES = {
    'AMSTERDAM', 'AMSTELLAND', 'BUIKSLOOT', 'DIEMEN', 'HOLYSLOOT', 'HOUTRIJK',
    'LEIMUIDEN', 'NIEUWENDAM', 'NIEUWER-AMSTEL', 'OSDORP', 'OUDERKERK',
    'POLANEN', 'RANSDORP', 'SCHELLINGWOUDE', 'SLOTEN', 'SLOTERDIJK',
    'VRIEZEKOOP', 'DE VRIJE GEER', 'WATERGRAAFSMEER', 'ZUNDERDORP'
}

## Possible fieldnames
# All fields that are filled in in the document. This list is taken from
# page 26 in the original document. Changed here and in the text extraction are
# variants of the keys such as `familierelaties` (plural) and `nevenfunctie`
# (singular) that are not listed on page 26. The plural is used in this script.
# Also, the phrase 'zijn klerken waren' does not occur in the document. Instead
# 'zijn klerk was' is used.
FIELDS = {
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
    'familierelaties': "",
    'adres':
    "Uit de ambtsperiode. Indien deze niet bekend is, zijn ook de daaraan voorafgaande of nakomende straatnamen opgenomen. De vier grote grachten zijn opgedeeld aan de hand van nadere adres aanduidingen. Het kantooradres heeft voorrang boven het huisadres. Achter de straatnaam is zo nodig tussen haakjes de huidige naam vermeld.",
    'godsdienst': "",
    'was klerk bij': "",
    'studie': "",
    'vreemde talen in zijn protocol': "",
    'vreemde talen welke hij kende': "",
    'zijn klerk was': "",
    'nevenfuncties': "De andere functies tijdens zijn leven.",
    'herkomst': "",
    'geboren': "",
    'doop': "",
    'ondertrouw': "",
    'huwelijk': "",
    'gescheiden': "",
    'overlijden': "",
    'begraven': ""
}

# TODO For mapping to LICR? https://druid.datalegend.net/dataLegend/LICR/
RELIGIONS = {
    'gereformeerd (hervormd)', 'rooms-katholiek', 'remonstrants',
    'Waals hervormd', 'Engels presbyteriaans', 'luthers', 'joods'
}


def main():

    with open(FILE, encoding='utf-8') as infile:
        lines = infile.read().split('\n')

    # First, get a mapping of notary information to page (for provenance sake),
    # a mapping to city (back-references not in there) and create a general
    # `notaries` dictionary that is going to be filled in.
    notaries, notary2page, notary2city = getNotariesNotary2Page2City(lines)

    # Then, remove the page references from the line collection
    lines = [i for i in lines if not i.startswith('<pagina')]

    # Then, remove the city references
    lines = [i for i in lines if not i in CITIES]

    # And remove the back-references
    lines = [i for i in lines if ': zie ' not in i]

    # Split the file in chunks of lines, each containing the info on one notary
    notaryLines = splitNotaries(lines)

    for n, lines in enumerate(notaryLines, 1):
        notaries = parseNotary(lines, n=n, notaries=notaries)

    return notaries


def getNotariesNotary2Page2City(lines):
    """Build a dictionary that contains information for each notary. Keep track 
    of the page the notary was described and the city section in which he was
    mentioned (for provenance). 
    
    Args:
        lines (str): Lines as coming from the txt file.
    
    Returns:
        tuple: dictionary of dictionaries of fields, a mapping of notaryNumber 
        to page(s), a mapping of notaryNumber to city/cities.
    """

    notaries = dict()
    notary2page = defaultdict(list)
    notary2city = defaultdict(list)

    notaryNumber = None
    for line in lines:
        if line in CITIES:
            city = line.lower().title()
        elif '<pagina' in line:
            page = re.findall(r'pagina (\d+)', line)[0]

            # In case the notary is described on two pages
            if notaryNumber is not None:
                notary2page[notaryNumber].append(page)
        else:
            match = re.findall(r'^(\d+)\. (.*)', line)
            if match != []:
                notaryNumber = int(match[0][0])
                name = match[0][1]

                notaries[notaryNumber] = {'literalName': name}
                notary2page[notaryNumber].append(page)
                notary2city[notaryNumber].append(city)

    # back-references to cities
    names2notaries = {notaries[i]['literalName']: i for i in notaries}

    for line in lines:
        if ': zie ' in line:
            name, city = line.split(': zie ')

            notary2city[names2notaries[name]].append(city)

    return notaries, notary2page, notary2city


def splitNotaries(lines):
    """Segment the txt file into chunks of information for one notary.
    
    Args:
        lines (list): lines from the txt file
    
    Returns:
        list: list of lists, each with lines for one notary
    """

    notaryLines = []

    notaryInfo = []
    for i in lines:
        if i == '' and notaryInfo != []:
            notaryLines.append(notaryInfo)
            notaryInfo = []
        elif i != '':
            notaryInfo.append(i)

    return notaryLines


def parseNotary(chunk, n=None, notaries=None):
    """Parse notary information for each notary chunk and return a dictionary.
    
    Fields parsed are:
        - birth
        - baptism
        - death
        - intended marriage
        - marriage
        - divorce
        - appointment
        - admission
        - commission
        - mentioned as notary
        - bankrupcy
        - withdrawal
        - address(es)
        - religion(s)
        -foreign language(s)

    Args:
        chunk (list): lines from the text file beloning to one notary
        n (int, optional): notaryNumber. Defaults to None.
        notaries (dict, optional): Dictionary to be filled. Defaults to None.
    
    Returns:
        dict: A filled dictionary with information on the notary. 
    """

    # Correct the line breaks
    chunk = correctChunk(chunk)

    # Add to dictionary
    for c in chunk[1:]:  # we can skip the first line that lists the name
        for f in FIELDS:
            if c.startswith(f):
                notaries[n][f] = c.split(': ')[1]

    ## birth
    # field = 'geboren'
    if notaries[n].get('geboren'):
        birthDate = notaries[n]['geboren']
        date = getDate(birthDate)

        notaries[n]['birthDate'] = date

    ## baptism
    # field = 'doop'
    if notaries[n].get('doop'):
        baptismDate = notaries[n]['doop']
        date = getDate(baptismDate)

        notaries[n]['baptismDate'] = date

    ## death
    # field = 'overlijden'
    if notaries[n].get('overlijden'):
        deathDate = notaries[n]['overlijden']
        date = getDate(deathDate)

        notaries[n]['deathDate'] = date

    ## intended marriage
    # field = 'ondertrouw'
    if notaries[n].get('ondertrouw'):
        intendedMarriageDate = notaries[n]['ondertrouw']
        date = getDate(intendedMarriageDate)

        notaries[n]['intendedMarriageDate'] = date

    ## marriage
    # field = 'huwelijk'
    if notaries[n].get('huwelijk'):
        marriageDate = notaries[n]['huwelijk']
        date = getDate(marriageDate)

        notaries[n]['marriageDate'] = date

    ## divorce
    # field = 'gescheiden'
    if notaries[n].get('gescheiden'):
        divorceDate = notaries[n]['gescheiden']
        date = getDate(divorceDate)

        notaries[n]['divorceDate'] = date

    ## appointment
    # field = 'benoeming'
    if notaries[n].get('benoeming'):
        appointmentDate = notaries[n]['benoeming']
        date = getDate(appointmentDate)

        notaries[n]['appointmentDate'] = date

    ## admission
    # field = 'admissie'
    if notaries[n].get('admissie'):
        admissionString = notaries[n]['admissie']
        if '; ' in admissionString:
            admissions = admissionString.split('; ')
        else:
            admissions = [admissionString]

        dates = []
        nominatedBys = []

        for admission in admissions:
            if ' op nominatie van ' in admission:
                admissionDate, nominatedBy = admission.split(
                    ' op nominatie van ')
                dates.append(getDate(admissionDate))
                nominatedBys.append(nominatedBy)
            else:
                dates.append(getDate(admission))
                nominatedBys.append(None)

        notaries[n]['admissionDate'] = dates
        notaries[n]['nominatedBy'] = nominatedBys

    ## commission
    # field = 'aanstelling'
    if notaries[n].get('aanstelling'):
        commissionDate = notaries[n]['aanstelling']
        date = getDate(commissionDate)

        notaries[n]['commissionDate'] = date

    ## mentioned as notary
    # field = 'vermeld als notaris'
    if notaries[n].get('vermeld als notaris'):
        mentionedAsNotaryDate = notaries[n]['vermeld als notaris']
        date = getDate(mentionedAsNotaryDate)

        notaries[n]['mentionedAsNotaryDate'] = date

    ## bankrupcy
    # field = 'faillissement'
    if notaries[n].get('faillissement'):
        bankrupcyDate = notaries[n]['faillissement']
        date = getDate(bankrupcyDate)

        notaries[n]['bankrupcyDate'] = date

    ## withdrawal
    # field = 'ambtsbeëindiging'
    if notaries[n].get('ambtsbeëindiging'):
        withdrawalString = notaries[n]['ambtsbeëindiging']
        # date = getDate(withdrawalDate)
        match = re.split(r'( \d{1,2} )', withdrawalString, 1)

        if len(match) == 1:
            withdrawalDate = match[0]
            withdrawalReason = None
        else:
            withdrawalDate, splittoken, withdrawalReason = match
            withdrawalDate += splittoken

        date = getDate(withdrawalDate)

        notaries[n]['withdrawalDate'] = date
        notaries[n]['withdrawalReason'] = withdrawalReason

    ## addresses
    # field = 'adres'
    if notaries[n].get('adres'):
        addressString = notaries[n]['adres']
        if '; ' in addressString:
            adresses = addressString.split('; ')
        else:
            adresses = [addressString]

        notaries[n]['adresses'] = adresses

    ## relgions
    # field = 'godsdienst'
    if notaries[n].get('godsdienst'):
        religionString = notaries[n]['godsdienst']
        if '; ' in religionString:
            religions = religionString.split('; ')
        else:
            religions = [religionString]

        notaries[n]['religions'] = religions

    ## foreign languages
    # field = 'vreemde talen in zijn protocol'
    if notaries[n].get('vreemde talen in zijn protocol'):
        languageString = notaries[n]['vreemde talen in zijn protocol']
        if 'vreemde taal welke hij kende' in languageString:
            languageString = languageString.replace(
                'vreemde taal welke hij kende', '').strip()

        if ', ' in languageString:
            foreignLanguages = languageString.split(', ')
        else:
            foreignLanguages = [languageString]

        notaries[n]['foreignLanguages'] = foreignLanguages

    return notaries


def correctChunk(chunk):
    """Try to fix the line breaks created by the PDF-columns in the document.
    
    Args:
        chunk (list): List of lines from one notary.
    
    Returns:
        list: A list of lines in which each line represents one type of 
        information, indicated by the field types in FIELDS. 
    """
    new_chunk = []

    previous_c = ""
    for c in chunk:
        if ':' in c and c.split(':')[0] in FIELDS:
            new_chunk.append(previous_c.strip())
            previous_c = c
        else:
            previous_c += " " + c

    return new_chunk


def getDate(datestring):
    """Try to parse a date string and return an isodate (8601).
    
    Args:
        datestring (str): The date as string
    
    Returns:
        str: iso-8601 formatted date. Returns a tuple if multiple dates are 
        found. Returns None if no date is found. 
    """

    if '; ' in datestring:
        dates = tuple(
            getDate(d) for d in datestring.split('; ')
            if getDate(d) is not None)
        if len(dates) > 1:
            return dates
        elif len(dates) == 1:
            return dates[0]
        else:
            return None

    # is there a place mentioned?
    if ' te ' in datestring:
        datestring, place = datestring.split(' te ')  #TODO place?

    if ' of ' in datestring:
        return tuple(getDate(d) for d in datestring.split(' of '))

    if ', ' in datestring:
        datestring, rest = datestring.rsplit(', ', 1)  #TODO comment?

    parsedate = dateparser.parse(datestring)
    if parsedate is None:
        return None

    # standard, today's date and month are added if there is only a year parsed.
    if parsedate.day == datetime.now().day and parsedate.month == datetime.now(
    ).month:
        return f"{parsedate.year}"

    elif parsedate.day == datetime.now().day:
        return f"{parsedate.year}-{str(parsedate.month).zfill(2)}"
    else:
        return f"{parsedate.year}-{str(parsedate.month).zfill(2)}-{str(parsedate.day).zfill(2)}"


if __name__ == "__main__":
    notaries = main()

    import pandas as pd

    df = pd.DataFrame(notaries)
    df.to_csv('data/notaries.csv')