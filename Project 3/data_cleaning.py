import xml.etree.cElementTree as ET
from collections import defaultdict
from bs4 import BeautifulSoup
import re
import pprint

OSMFILE = "test_sample.xml"
html_file = 'ZipCodes.html'
street_type_re = re.compile(r'\b\S+\.?$', re.IGNORECASE)
zipcode_search = re.compile(r'^([0-9]+)-([0-9]+)')
prefix_zip = re.compile(r'^[GA\s]+([0-9]+)')
problemchars = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')
county_search = re.compile(r'(^[a-zA-z]+),*')

expected = ['Southwest', 'Southeast', 'Northeast','Northwest']
CREATED = [ "version", "changeset", "timestamp", "user", "uid"]
direction_mapping = { "S": "South",
            "W": "West",
            "E" : 'East',
            "N" : 'North',
            "NE" : "Northeast",
            "NW" : "Northwest",
            "SE" : "Southeast",
            "SW" : "Southwest"}
mapping = {"Dr" : "Drive", 
           "St": "Street",
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

def is_street_name(elem):
    return (elem.attrib['k'] == "addr:street")
def gen_created_dict(element):
    d = {}
    for key in CREATED:
        value = element.get(key)
        d[key] = value
    #print d
    return d
def is_direction(direction):
    return direction in direction_mapping.keys()
def is_postcode(elem):
    return (elem.attrib['k'] == "addr:postcode")
def is_county(elem):
    return (elem.attrib['k'] == "addr:county")

def gen_address_dict(elem):
    d = {}
    for tag in elem.iter("tag"):
        key_val = tag.attrib['k']
        if is_street_name(tag):
            clean_street_type(d,tag)
        elif is_postcode(tag):
            clean_postcode(d, tag)
        elif is_county(tag):
            clean_county(d, tag)
        elif key_val.find('addr:') != -1:
            k = key_val[5:]
            if k == 'housenumber':
                d[k] = int(tag.attrib['v'])
            else:   
                d[k] = tag.attrib['v']
    return d
def handle_non_addr_tags(element,node):
    for tag in element.iter("tag"):
        key_val = tag.attrib['k']
        val = tag.attrib['v']
        if problemchars.search(key_val) or key_val.find(':') != -1:
            continue
        if key_val.find('addr:') == -1:
            node[key_val] = val
    
def clean_street_type(d,tag):
    street_name = tag.attrib['v']
    m = street_type_re.search(street_name)
    if m:
        street_type = m.group()
        pos = street_name.find(street_type)
        if is_direction(street_type) or street_type in expected :
            d['streetSuffix'] = direction_mapping[street_type]
            street_name = street_name[:pos-1]
            m = street_type_re.search(street_name)
            street_type = m.group()
            pos = street_name.find(street_type)
            
        if street_type in mapping:
            d['street'] = street_name[:pos] + mapping[street_type] 
        else:
            d['street'] = street_name
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
def update_zipInAtanta_field(d,zip,zcodes):
    if zip in zcodes:
        d['zipInAtlanta'] = 'T'
    else:
        d['zipInAtlanta'] = 'F'
def clean_postcode(d,tag): 
    zcodes = extract_zip_codes(html_file)
    m = zipcode_search.search(tag.attrib['v'])
    m_ = prefix_zip.search(tag.attrib['v'])
    if m:
        zip = m.group(1)
        ext = m.group(2)
        d['postcode'] = int(zip)
        d['postcodeExt'] = int(ext)
        update_zipInAtanta_field(d, zip, zcodes)
    elif m_:
        zip = m_.group(1)
        d['postcode'] = int(zip)
        update_zipInAtanta_field(d, zip, zcodes)
    else:
        d['postcode'] = int(tag.attrib['v'])
        update_zipInAtanta_field(d, tag.attrib['v'], zcodes) 
def clean_county(d,tag):
    m = county_search.search(tag.attrib['v'])
    if m:
        county = m.group(1)
        d['county'] = county
    else:
        d['county'] = tag.attrib['v']
def address_present(element):
    for tag in element.iter("tag"):
        key_val = tag.attrib['k']
        if key_val.find('addr:') != -1:
            return True
    return False     
def gen_pos_array(element):
    pos = []
    val = element.get('lat')
    #print type(val)
    if val != None:
        pos.append(float(val))
    val = element.get('lon')
    if val != None:
        pos.append(float(val))
    return pos 
def is_pos_present(element):
    return element.get('lat') != None and element.get('lon') != None  
def gen_node_refs_array(element):
    l = []
    for tag in element.iter("nd"):
        ref = tag.attrib['ref']
        l.append(ref)
    return l        
def clean_file(osmfile):
    osm_file = open(osmfile, 'r')
    for event, elem in ET.iterparse(osm_file, events=("start",)):
        if elem.tag == "node" or elem.tag == "way":
            d = {}
            d['created'] = gen_created_dict(elem)
            if is_pos_present(elem):
                d['pos'] = gen_pos_array(elem)
            if address_present(elem):
                d['address'] = gen_address_dict(elem)
            handle_non_addr_tags(elem, d)
            if elem.tag == 'way':
                d['node_refs'] = gen_node_refs_array(elem)
            pprint.pprint(d)
if __name__ == '__main__':
    clean_file(OSMFILE)