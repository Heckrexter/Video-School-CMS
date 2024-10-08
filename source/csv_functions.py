import csv
import datetime
from type_vars import *

# FORMAT FOR CSV: [id, title, url, shoot_timestamp, edit_timestamp, upload_timestamp, comment]
# Function that takes the location of the csv file and returns a list of the csv file
def handle_csv(url):
    sqllist=[]
    # opens the csv file and reads it
    with open(url, "r"  , encoding='utf-8') as csvfile:
        rows = csv.reader(csvfile, dialect="excel")
        rows = list(rows)
        for i in range(0, len(rows)):
            # skip row if name or id are empty
            if rows[i][0] == "":
                continue
            if rows[i][1] == "":
                continue
            sqllist.append(rows[i])
    # returs csv file as a list with no empty rows
    return sqllist

# Check the csv formatting and validity of entries such as time and status
def check_n_format_csv(csv_list, import_format=None):
    # check the top row for formatting
    head = csv_list[0]
    if len(head) != 6:
        return "Too many elements per row please recheck"
    if head[0][1:] != 'Video No.' or head[1] != 'Title' or head[2] != 'Shoot Date' or head[3] != 'Edit Date' or head[4] != "Upload Date" or head[5] != 'Comments':
        return "FIX TABLE HEADERS"
    
    # Create a list to store output csv file
    resulting_csv_list = []
    # checking all data entries and append the valid ones
    for i in range(1, len(csv_list)):
        row = csv_list[i]
        if type(row[0]) != str:
            return "ID column at row "+str(i)+" is not an str"
        else:
            if row[0].isdigit() == False:
                return "invalid id entry at row "+str(i)
        if import_format == True:
            if row[2] != "":
                try:
                    row[2] = int(datetime.datetime.strptime(row[2], '%d-%b-%y').timestamp())
                    if row[3] != "":
                        try:
                            row[3] = int(datetime.datetime.strptime(row[3], '%d-%b-%y').timestamp())
                            if row[4] != "":
                                try:
                                    row[4] = int(datetime.datetime.strptime(row[4], '%d-%b-%y').timestamp())
                                except Exception as e:
                                    return "error on row "+row[0]+" at shoot timestamp "+row[4]+" Error: "+str(e)
                        except Exception as e:
                            return "error on row "+row[0]+" at shoot timestamp "+row[3]+" Error: "+str(e)
                except Exception as e:
                    return "error on row "+row[0]+" at shoot timestamp "+row[2]+" Error: "+str(e)
        if row[2] != "" and row[3] != "" and row[4] != "" :
            row.append(VIDEO_STATUS_UPLOADED)
        elif row[2] != "" and row[3] != "" and row[4] == "":
            row.append(VIDEO_STATUS_EDITED)
        elif row[2] != "" and row[3] == "" and row[4] == "":
            row.append(VIDEO_STATUS_SHOT)
        elif row[2] == "" and row[3] == "" and row[4] == "":
            row.append(VIDEO_STATUS_TO_BE_CREATED)
        else:
            return "Error with dates on row "+row[0]
        resulting_csv_list.append(row)
    return resulting_csv_list