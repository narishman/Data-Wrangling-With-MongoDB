#!/usr/bin/env python
# -*- coding: utf-8 -*-
# All your changes should be in the 'extract_airports' function
# It should return a list of airport codes, excluding any combinations like "All"

from bs4 import BeautifulSoup
html_page = "options.html"


def extract_airports(page):
    data = []
    with open(page, "r") as html:
        # do something here to find the necessary values
        soup = BeautifulSoup(html)
        entries = soup.find(id="AirportList")
        l = entries.find_all_next("option")
        print l
        for a in l:
          t = a["value"]
          if t != "selected" and t != "AllMajors" and t != "AllOthers" and t != "All":
                print t
                data.append(t)
    return data


def test():
    data = extract_airports(html_page)
    assert len(data) == 15
    assert "ATL" in data
    assert "ABR" in data

test()