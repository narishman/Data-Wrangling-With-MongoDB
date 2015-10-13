#!/usr/bin/env python
"""
Your task is as follows:
- read the provided Excel file
- find and return the min, max and average values for the COAST region
- find and return the time value for the min and max entries
- the time values should be returned as Python tuples

Please see the test function for the expected return format
"""

import xlrd
from zipfile import ZipFile
datafile = "2013_ERCOT_Hourly_Load_Data.xls"


def open_zip(datafile):
    with ZipFile('{0}.zip'.format(datafile), 'r') as myzip:
        myzip.extractall()

def get_max_value(sheet):
    row = 0
    max_value = 0.0
    l = sheet.col_values(1, start_rowx=1, end_rowx=sheet.nrows)
    for i,val in enumerate(l):
        if(val > max_value):
            max_value = val
            row = i + 1
   
    return row,max_value
        
def get_min_value(sheet,max_value):
    row = 0
    min_value = max_value
    l = sheet.col_values(1, start_rowx=1, end_rowx=sheet.nrows)
    for i,val in enumerate(l):
        if(val < min_value):
            min_value = val
            row = i + 1
    return row,min_value    

def get_avg_coast(sheet):
    sum_val = 0.0
    l = sheet.col_values(1, start_rowx=1, end_rowx=sheet.nrows)
    for val in l:
        sum_val = sum_val + val
    num = sheet.nrows - 1
    return sum_val/num 


def parse_file(datafile):
    workbook = xlrd.open_workbook(datafile)
    sheet = workbook.sheet_by_index(0)

    ### example on how you can get the data
    #sheet_data = [[sheet.cell_value(r, col) for col in range(sheet.ncols)] for r in range(sheet.nrows)]

    ### other useful methods:
    # print "\nROWS, COLUMNS, and CELLS:"
    # print "Number of rows in the sheet:", 
    # print sheet.nrows
    # print "Type of data in cell (row 3, col 2):", 
    # print sheet.cell_type(3, 2)
    # print "Value in cell (row 3, col 2):", 
    # print sheet.cell_value(3, 2)
    # print "Get a slice of values in column 3, from rows 1-3:"
    # print sheet.col_values(3, start_rowx=1, end_rowx=4)

    # print "\nDATES:"
    # print "Type of data in cell (row 1, col 0):", 
    # print sheet.cell_type(1, 0)
    # exceltime = sheet.cell_value(1, 0)
    # print "Time in Excel format:",
    # print exceltime
    # print "Convert time to a Python datetime tuple, from the Excel float:",
    # print xlrd.xldate_as_tuple(exceltime, 0)
    
    
    data = {
            'maxtime': (0, 0, 0, 0, 0, 0),
            'maxvalue': 0,
            'mintime': (0, 0, 0, 0, 0, 0),
            'minvalue': 0,
            'avgcoast': 0
    }
    row,max_value = get_max_value(sheet)
#    print row, max_value
    maxtime = sheet.cell_value(row,0)
 #   print maxtime
    data['maxtime'] = xlrd.xldate_as_tuple(maxtime,0)
    data['maxvalue'] = sheet.cell_value(row,1)
    row,min_value = get_min_value(sheet,max_value)
    mintime = sheet.cell_value(row,0)
    data['mintime'] = xlrd.xldate_as_tuple(mintime,0)
    data['minvalue'] = sheet.cell_value(row,1)
    data['avgcoast'] = get_avg_coast(sheet)
    print data    
    return data


def test():
    open_zip(datafile)
    data = parse_file(datafile)

    assert data['maxtime'] == (2013, 8, 13, 17, 0, 0)
    assert round(data['maxvalue'], 10) == round(18779.02551, 10)


test()