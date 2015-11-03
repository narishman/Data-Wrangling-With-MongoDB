import xml.etree.cElementTree as ET
from collections import defaultdict
import re
import pprint

OSMFILE = "sample.osm"
street_type_re = re.compile(r'\b\S+\.?$', re.IGNORECASE)

expected = ['Southwest', 'Southeast', 'Northeast','Northwest']

direction_mapping = { "S": "South",
            "W": "West",
            "E" : 'East',
            "N" : 'North',
            "NE" : "Northeast",
            "NW" : "Northwest",
            "SE" : "Southeast",
            "SW" : "Southwest"}
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

def is_street_name(elem):
    return (elem.attrib['k'] == "addr:street")

def create_direction_tag(direction):
    return "<tag k=\'addr:direction\', v=\'{0}\'\\>".format(direction)
def clean_street_type(d,tag):
    street_name = tag.attrib['v']
    m = street_type_re.search(street_name)
    if m:
        street_type = m.group()
        pos = street_name.find(street_type)
        if street_type in expected:
            d['street'] = street_name[:pos-1]
            d['direction'] = street_type
        elif street_type in direction_mapping.keys():
            d['street'] = street_name[:pos-1]
            d['direction'] = direction_mapping[street_type]
        elif street_type in mapping:
            d['street'] = street_name[:pos] + mapping[street_type] 
        else:
            d['street'] = street_name    
def clean_file(osmfile):
    osm_file = open(osmfile, 'r')
    for event, elem in ET.iterparse(osm_file, events=("start",)):
        if elem.tag == "node" or elem.tag == "way":
            d = {}
            for tag in elem.iter("tag"):
                if is_street_name(tag):
                    clean_street_type(d,tag)
                    pprint.pprint(d)
if __name__ == '__main__':
    clean_file(OSMFILE)