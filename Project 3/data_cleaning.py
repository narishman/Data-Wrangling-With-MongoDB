import xml.etree.cElementTree as ET
from collections import defaultdict
from bs4 import BeautifulSoup
import re
import pprint
from pymongo import MongoClient
    
OSMFILE = "sample.osm"
#OSMFILE = 'C:\\Users\\rmhyman\\Documents\\atlanta_georgia.osm'
#OSMFILE = 'C:\\Users\\ransf\\Documents\\atlanta_georgia.osm'
#OSMFILE = "test_sample.xml"
html_file = 'ZipCodes.html'
street_type_re = re.compile(r'\b\S+\.?$', re.IGNORECASE)
zipcode_search = re.compile(r'^([0-9]+)-([0-9]+)')
prefix_zip = re.compile(r'^[GA]+\s*([0-9]+)')
has_zip_search = re.compile(r'[0-9]+')
problemchars = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')
county_search = re.compile(r'(^[a-zA-z]+),*')
house_num_search = re.compile(r'^([0-9]+)*')

def extract_zip_codes(page):
    '''
    The purpose of this function is to perform the screen scraping 
    task of collecting all of the zip codes that reside in the city of Atlanta
    '''
    data = []
    with open(page, 'r') as html:
        soup = BeautifulSoup(html)
        #print soup.head
        tables = soup.find_all(href=re.compile(r'http://www.zipcodestogo.com/Atlanta/GA/*'))
        #print tables
        for table in tables:
            data.append(table.text)

    return data
#zcodes is the global variable used to store the golden-standard list of zipcodes within the Atlanta city limits
zcodes = extract_zip_codes(html_file)
expected = ['Southwest', 'Southeast', 'Northeast','Northwest']
CREATED = [ "version", "changeset", "timestamp", "user", "uid"]
direction_mapping = { "S": "South",
            "W": "West",
            "E" : 'East',
            "N" : 'North',
            "NE" : "Northeast",
            "NW" : "Northwest",
            "SE" : "Southeast",
            "SW" : "Southwest",
            }
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

#This function determines whether this tag is a street name or not
def is_street_name(elem):
    return (elem.attrib['k'] == "addr:street")
#This function creates the user document which generates key/value pairs
# for entries within the CREATED global variable
def gen_created_dict(element):
    d = {}
    for key in CREATED:
        value = element.get(key)
        d[key] = value
    #print d
    return d
#This function is used to determine whether last word of the street name is a ordinal direction
#i.e Southwest, Northeast, etc...
def is_direction(direction):
    return direction in direction_mapping.keys()
#This function determines whether this tag represents a postal code entry
def is_postcode(elem):
    return (elem.attrib['k'] == "addr:postcode")
#This function determines whether this tag represents a county entry
def is_county(elem):
    return (elem.attrib['k'] == "addr:county")
'''
This function generates the address document
The final structure should look like:
address : {
    "street" : "Waterstone Way",
    "housenumber" : 200,
    "postcode" : 30076,
    "streetSuffix" : "Southwest"
    "zipInAtlanta" : "T"
Note that we check whether the information actually exists.  
If it does not exist, we do not create an entry
'''
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
                m = house_num_search.search(tag.attrib['v'])
                if m and len(m.group(0)) != 0:
                    #print tag.attrib['v']
                    d[k] = int(m.group(1))
            else:   
                d[k] = tag.attrib['v']
                
    return d
#This function generates the remainder key/value pairs
#As long as there are no problematic chars in it's key name.
def handle_non_addr_tags(element,node):
    for tag in element.iter("tag"):
        key_val = tag.attrib['k']
        if problemchars.search(key_val) or key_val.find(':') != -1:
            continue
        if key_val.find('addr:') == -1:
            node[key_val] = tag.attrib['v'] 
'''
This function cleans up the street type by first checking whether an
street suffix exists.  If it does then it places it within the streetSuffix
field and then searches for street_type.  Then it cleans the street_type.
If there is no street_suffix, then it just cleans the street type
'''                
def clean_street_type(d,tag):
    street_name = tag.attrib['v']
    m = street_type_re.search(street_name)
    if m:
        street_type = m.group()
        pos = street_name.find(street_type)
        in_expected = street_type in expected
        if is_direction(street_type) or in_expected == True :
            if in_expected == False:
                d['streetSuffix'] = direction_mapping[street_type]
            else:
                d['streetSuffix'] = street_type
            street_name = street_name[:pos-1]
            m = street_type_re.search(street_name)
            street_type = m.group()
            pos = street_name.find(street_type)
            
        if street_type in mapping:
            d['street'] = street_name[:pos] + mapping[street_type] 
        else:
            d['street'] = street_name

def update_zipInAtanta_field(d,zip):
    '''
    This function checks the golden list of Atlanta zip codes collected from 
    zipcodestogo.com and sets the field zipInAtlanta appropriately
    '''
    if zip in zcodes:
        d['zipInAtlanta'] = 'T'
    else:
        d['zipInAtlanta'] = 'F'
def clean_postcode(d,tag): 
    '''
    This function cleans the zipcodes entries.  If the postcode extension is present, 
    then it places it in the postcodeExt field
    There are 3 regex that are performed:
    One checks for whether it is in the 9 digit representation
    Another checks whether state code prefixes the zipcode
    The last one checks whether a zip codes is actually present as some were not
    '''
    m = zipcode_search.search(tag.attrib['v'])
    m_ = prefix_zip.search(tag.attrib['v'])
    M = has_zip_search.search(tag.attrib['v'])
    if m:
        zip = m.group(1)
        ext = m.group(2)
        d['postcode'] = int(zip)
        d['postcodeExt'] = int(ext)
        update_zipInAtanta_field(d, zip)
    elif m_:
        zip = m_.group(1)
        d['postcode'] = int(zip)
        update_zipInAtanta_field(d, zip)
    elif M:
        #print tag.attrib['v']
        zip = M.group()
        d['postcode'] = int(zip)
        update_zipInAtanta_field(d, zip) 
#This function removes parses out the actual county name since many of the
#entries had the state code in them as well
def clean_county(d,tag):
    m = county_search.search(tag.attrib['v'])
    if m:
        county = m.group(1)
        d['county'] = county
    else:
        d['county'] = tag.attrib['v']
#This function checks whether address data is present        
def address_present(element):
    if element.tag == 'way':
        return False
    for tag in element.iter("tag"):
        key_val = tag.attrib['k']
        if key_val.find('addr:') != -1:
            return True
    return False     
#This function generates a latitude/longitude pair within the "pos" entry
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
#This function checks whether the latitude and longitude values are present 
def is_pos_present(element):
    return element.get('lat') != None and element.get('lon') != None

#This function generates a node reference array from the "way" XML documents  
def gen_node_refs_array(element):
    l = []
    for tag in element.iter("nd"):
        ref = tag.attrib['ref']
        l.append(ref)
    return l        
#@profile
def clean_file(osmfile):
    osm_file = open(osmfile, 'r')
    client = MongoClient("mongodb://localhost:27017")
    db = client.osm
    context = ET.iterparse(osm_file, events=("start",))
    context = iter(context)
    event,root = context.next()
    for  event,elem in context:
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
            #pprint.pprint(d)
            #data.append(d)
            db.atlanta.insert(d)
            root.clear()
            
            
    #return data
def tiger_present(element):
    '''
    Tiger entries were very abundant in this dataset, 
    so I used this function to audit it. These entries were not cleaned in this project
    '''
    if element.tag == 'way':
        return False
    for tag in element.iter("tag"):
        key_val = tag.attrib['k']
        if key_val.find('tiger:') != -1:
            return True
    return False 
def audit_tiger_entries(osm_file):
    '''
    This function was not used in this project.  Just used to examine the dataset
    '''
    context = ET.iterparse(osm_file, events=("start",))
    context = iter(context)
    event,root = context.next()
    count = 0
    for  event,elem in context:
        if elem.tag == "node" or elem.tag == "way":
            if tiger_present(elem):
                count += 1
        root.clear()
    print "Number of entries with tiger data: ", count
def insert_data(data):
    client = MongoClient("mongodb://localhost:27017")
    db = client.samplemap
    db.sample.insert(data)
    
if __name__ == '__main__':
    clean_file(OSMFILE)
