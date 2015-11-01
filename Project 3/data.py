#!/usr/bin/env python
# -*- coding: utf-8 -*-
import xml.etree.cElementTree as ET
import pprint
import re
import codecs
import json
"""
Your task is to wrangle the data and transform the shape of the data
into the model we mentioned earlier. The output should be a list of dictionaries
that look like this:

{
"id": "2406124091",
"type: "node",
"visible":"true",
"created": {
          "version":"2",
          "changeset":"17206049",
          "timestamp":"2013-08-03T16:43:42Z",
          "user":"linuxUser16",
          "uid":"1219059"
        },
"pos": [41.9757030, -87.6921867],
"address": {
          "housenumber": "5157",
          "postcode": "60625",
          "street": "North Lincoln Ave"
        },
"amenity": "restaurant",
"cuisine": "mexican",
"name": "La Cabana De Don Luis",
"phone": "1 (773)-271-5176"
}

You have to complete the function 'shape_element'.
We have provided a function that will parse the map file, and call the function with the element
as an argument. You should return a dictionary, containing the shaped data for that element.
We have also provided a way to save the data in a file, so that you could use
mongoimport later on to import the shaped data into MongoDB. 

Note that in this exercise we do not use the 'update street name' procedures
you worked on in the previous exercise. If you are using this code in your final
project, you are strongly encouraged to use the code from previous exercise to 
update the street names before you save them to JSON. 

In particular the following things should be done:
- you should process only 2 types of top level tags: "node" and "way"
- all attributes of "node" and "way" should be turned into regular key/value pairs, except:
    - attributes in the CREATED array should be added under a key "created"
    - attributes for latitude and longitude should be added to a "pos" array,
      for use in geospacial indexing. Make sure the values inside "pos" array are floats
      and not strings. 
- if second level tag "k" value contains problematic characters, it should be ignored
- if second level tag "k" value starts with "addr:", it should be added to a dictionary "address"
- if second level tag "k" value does not start with "addr:", but contains ":", you can process it
  same as any other tag.
- if there is a second ":" that separates the type/direction of a street,
  the tag should be ignored, for example:

<tag k="addr:housenumber" v="5158"/>
<tag k="addr:street" v="North Lincoln Avenue"/>
<tag k="addr:street:name" v="Lincoln"/>
<tag k="addr:street:prefix" v="North"/>
<tag k="addr:street:type" v="Avenue"/>
<tag k="amenity" v="pharmacy"/>

  should be turned into:

{...
"address": {
    "housenumber": 5158,
    "street": "North Lincoln Avenue"
}
"amenity": "pharmacy",
...
}

- for "way" specifically:

  <nd ref="305896090"/>
  <nd ref="1719825889"/>

should be turned into
"node_refs": ["305896090", "1719825889"]
"""


lower = re.compile(r'^([a-z]|_)*$')
lower_colon = re.compile(r'^([a-z]|_)*:([a-z]|_)*$')
problemchars = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')

CREATED = [ "version", "changeset", "timestamp", "user", "uid"]
'''
- if second level tag "k" value contains problematic characters, it should be ignored
- if second level tag "k" value starts with "addr:", it should be added to a dictionary "address"
- if second level tag "k" value does not start with "addr:", but contains ":", you can process it
  same as any other tag.
- if there is a second ":" that separates the type/direction of a street,
  the tag should be ignored, for example:

<tag k="addr:housenumber" v="5158"/>
<tag k="addr:street" v="North Lincoln Avenue"/>
<tag k="addr:street:name" v="Lincoln"/>
<tag k="addr:street:prefix" v="North"/>
<tag k="addr:street:type" v="Avenue"/>
<tag k="amenity" v="pharmacy"/>
'''
def address_present(element):
    for tag in element.iter("tag"):
        key_val = tag.attrib['k']
        if key_val.find('addr:') != -1:
            return True
    return False

def gen_address_dict(element):
    address = {}
    for tag in element.iter("tag"):
        key_val = tag.attrib['k']
        val = tag.attrib['v']
        if problemchars.search(key_val):
            continue
        if key_val.find('addr:street:') != -1:
            continue
        if key_val.find('addr:') != -1:
            k = key_val[5:]
            #print k
            #print val
            address[k] = val
    
    #pprint.pprint(address)        
    return address
def handle_non_addr_tags(element,node):
    for tag in element.iter("tag"):
        key_val = tag.attrib['k']
        val = tag.attrib['v']
        if problemchars.search(key_val):
            continue
        if key_val.find('addr:') == -1:
            node[key_val] = val
    return node
def gen_created_dict(element):
    d = {}
    for key in CREATED:
        value = element.get(key)
        d[key] = value
    #print d
    return d
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
def shape_element(element):
    node = {}
    if element.tag == "node" or element.tag == "way" :
        # YOUR CODE HERE
        node['created'] = gen_created_dict(element)
        for a in element.attrib:
            if a not in CREATED and a!= 'lon' and a != 'lat':
                value = element.get(a)
                node[a] = value
        node['pos'] = gen_pos_array(element)
        node['type'] = element.tag
        if address_present(element):
            node['address'] = gen_address_dict(element)
        node = handle_non_addr_tags(element,node)
        if element.tag == 'way':
            node['node_refs'] = gen_node_refs_array(element)
            
        pprint.pprint(node)
        return node
    else:
        return None
'''
- for "way" specifically:

  <nd ref="305896090"/>
  <nd ref="1719825889"/>
'''
def gen_node_refs_array(element):
    l = []
    for tag in element.iter("nd"):
        ref = tag.attrib['ref']
        l.append(ref)
    return l


def process_map(file_in, pretty = False):
    # You do not need to change this file
    file_out = "{0}.json".format(file_in)
    data = []
    with codecs.open(file_out, "w") as fo:
        for _, element in ET.iterparse(file_in):
            el = shape_element(element)
            if el:
                data.append(el)
                if pretty:
                    fo.write(json.dumps(el, indent=2)+"\n")
                else:
                    fo.write(json.dumps(el) + "\n")
    return data

def test():
    # NOTE: if you are running this code on your computer, with a larger dataset, 
    # call the process_map procedure with pretty=False. The pretty=True option adds 
    # additional spaces to the output, making it significantly larger.
    data = process_map('example.osm', True)
    pprint.pprint(data)
    

if __name__ == "__main__":
    test()