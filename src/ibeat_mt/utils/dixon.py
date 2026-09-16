import os
import pandas as pd
import csv


def download_record():

    # download dixon record csv from Github
    dixon_record_url = 'https://raw.githubusercontent.com//openmiblab//ppln-ibeat-totseg//refs//heads//main//data//dixon_data.csv'
    dixon_record = pd.read_csv(dixon_record_url)
    path = os.path.join(os.getcwd(), 'src', 'data')
    os.makedirs(path, exist_ok=True)
    dixon_record.to_csv(os.path.join(path, 'dixon_data.csv'), index=False)


def dixon_record():
    record = os.path.join(os.getcwd(), 'src', 'data', 'dixon_data.csv')
    with open(record, 'r') as file:
        reader = csv.reader(file)
        record = [row for row in reader]
    return record


def dixon_series_desc(record, patient, study):
    for row in record:
        if row[1] == patient:
            if row[2]==study:
                return row[5]
    raise ValueError(
        f'Patient {patient}, study {study}: not found in src/data/dixon_data.csv'
    )
