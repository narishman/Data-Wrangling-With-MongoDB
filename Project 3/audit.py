"""
Your task in this exercise has two steps:

- audit the OSMFILE and change the variable 'mapping' to reflect the changes needed to fix 
    the unexpected street types to the appropriate ones in the expected list.
    You have to add mappings only for the actual problems you find in this OSMFILE,
    not a generalized solution, since that may and will depend on the particular area you are auditing.
- write the update_name function, to actually fix the street name.
    The function takes a string with street name as an argument and should return the fixed name
    We have provided a simple test so that you see what exactly is expected
"""
import xml.etree.cElementTree as ET
from collections import defaultdict
from bs4 import BeautifulSoup
import re
import pprint

html_file = 'ZipCodes.html'
OSMFILE = "sample.osm"
street_type_re = re.compile(r'\b\S+\.?$', re.IGNORECASE)
has_numbers_in_type = re.compile(r'[0-9]+')


expected = ["Street", "Avenue", "Boulevard", "Drive", "Court", "Place", "Square", "Lane", "Road", 
            "Trail", "Parkway", "Commons",'Southwest','Southeast','Northwest','Northeast',"Way","Circle"]

# UPDATE THIS VARIABLE
mapping = { "St": "Street",
            "St.": "Street",
            "Ave" : 'Avenue',
            "Rd." : 'Road',
            "Rd" : 'Road',
            "Ln" : "Lane",
            "Trl" : 'Trail',
            "Xing" : 'Crossing',
            "Sq" : "Square",
            "Cir" : "Circle",
            "Pt" : "Point",
            "Pl" : "Place",
            "Ct" : "Court",
            "Blvd": "Boulevard",
            "Lndg" : "Landing",
            "Ave." : "Avenue",
            "Hwy" : "Highway"}
direction_mapping = { "S": "South",
            "W": "West",
            "E" : 'East',
            "N" : 'North',
            "NE" : "Northeast",
            "NW" : "Northwest",
            "SE" : "Southeast",
            "SW" : "Southwest"}

def extract_zip_codes(page):
    data = []
    with open(page, 'r') as html:
        soup = BeautifulSoup(html)
        #print soup.head
        tables = soup.find_all(href=re.compile(r'http://www.zipcodestogo.com/Atlanta/GA/*'))
        #print tables
        for table in tables:
            data.append(table.text)

    return data
def audit_street_type(street_types, street_name):
    m = street_type_re.search(street_name)
    if m:
        street_type = m.group()
        if street_type not in expected and street_type not in direction_mapping.keys() and street_type not in mapping.keys():
            found = has_numbers_in_type.search(street_type)
            if found:
                street_types[street_type].add(street_name)

def audit_key_values(key_vals,key_val):
        key_vals.add(key_val)
def audit_postcodes(post_codes,postcode):
    post_codes.add(postcode)
def audit_counties(counties,county):
    counties.add(county)        
def audit_tag_attribs(tag_names,tags):
    #this function is to check whether the 'k' and 'v' are the only attributes of the tags
    for tag_name in tags:
        tag_names.add(tag_name)
def is_street_name(elem):
    return (elem.attrib['k'] == "addr:street")
def is_postcode(elem):
    return (elem.attrib['k'] == "addr:postcode")
def is_county(elem):
    return (elem.attrib['k'] == "addr:county")


def audit(osmfile):
    osm_file = open(osmfile, "r")
    street_types = defaultdict(set)
    #tag_attribs = set()
    key_vals = set()
    post_codes = set()
    counties = set()
    for event, elem in ET.iterparse(osm_file, events=("start",)):
        if elem.tag == "node" or elem.tag == "way":
            for tag in elem.iter("tag"):
                #audit_tag_attribs(tag_attribs, tag.keys())
                audit_key_values(key_vals, tag.attrib['k'])
                if is_street_name(tag):
                    audit_street_type(street_types, tag.attrib['v'])
                elif is_postcode(tag):
                    audit_postcodes(post_codes, tag.attrib['v'])
                elif is_county(tag):
                    audit_counties(counties, tag.attrib['v'])
    return street_types,post_codes,key_vals,counties


def update_name(name, mapping):

    # YOUR CODE HERE
    #names = mapping.keys
    #print names
    for k in mapping.keys():
        pos = name.find(k)
        if pos != -1:
            name = name[:pos] + mapping[k]

    return name


def test():
    zc = extract_zip_codes(html_file)
    st_types,post_codes,key_vals,counties = audit(OSMFILE)
    for zipcode in post_codes:
        if zipcode not in zc:
            print zipcode
    #assert len(st_types) == 3
    #pprint.pprint(dict(st_types).keys())
    #pprint.pprint(dict(st_types))
    #pprint.pprint(post_codes)
    #pprint.pprint(counties)
    #pprint.pprint(key_vals)

    
if __name__ == '__main__':
    test()