import re
import csv
import sys
import os.path
import argparse

# allow large content in the dump

# returns if the line is an insert statement
def is_insert(line):
    return 'INSERT INTO' in line or False

# returns the values for a table
def get_values(line):
    return line.partition(' VALUES ')[2]

# returns the name of the table
def get_table_name(line):
    match = re.search('INSERT INTO `([0-9_a-zA-Z]+)`', line)
    if match:
        return match.group(1)
    else:
        print(line)

# get the name of the columns
def get_columns(line):
    match = re.search('INSERT INTO `.*` \(([^\)]+)\)', line)
    if match:
        return list(map(lambda x: x.replace('`', '').strip(), match.group(1).split(',')))

# checks if the value collection is correct
def values_sanity_check(values):
    assert values
    assert values[0] == '('
    # Assertions have not been raised
    return True

# returns the parsed values
def parse_values(values):
    rows = []
    latest_row = []

    reader = csv.reader([values], delimiter=',',
                        doublequote=False,
                        escapechar='\\',
                        quotechar="'",
                        strict=True
    )

    for reader_row in reader:
        for column in reader_row:
            if len(column) == 0 or column == 'NULL':
                latest_row.append(chr(0))
                continue
            if column[0] == "(":
                new_row = False
                if len(latest_row) > 0:
                    if latest_row[-1][-1] == ")":
                        latest_row[-1] = latest_row[-1][:-1]
                        new_row = True
                if new_row:
                    latest_row = ['' if field == '\x00' else field for field in latest_row]

                    rows.append(latest_row)
                    latest_row = []
                if len(latest_row) == 0:
                    column = column[1:]
            latest_row.append(column)
        if latest_row[-1][-2:] == ");":
            latest_row[-1] = latest_row[-1][:-2]
            latest_row = ['' if field == '\x00' else field for field in latest_row]

            rows.append(latest_row)

        return rows


def main(filepath, output_folder):
    
    # read the dump line by line
    with open(filepath, 'rb') as f:
        for line in f.readlines():
            try:
                line = line.decode("utf-8")

            except UnicodeDecodeError:
                line = str(line)
            if is_insert(line):
                table_name = get_table_name(line)
                columns = get_columns(line)
                values = get_values(line)
                if values_sanity_check(values):
                    rows = parse_values(values)
                    #print(rows)

                if not os.path.isfile(output_folder + table_name + '.csv'):
                    with open(output_folder + table_name + '.csv', 'w') as outcsv:
                        writer = csv.writer(outcsv, quoting=csv.QUOTE_ALL)
                        #writer.writerow(columns)
                        for row in rows:
                            writer.writerow(row)
                else:
                    with open(output_folder + table_name + '.csv', 'a') as outcsv:
                        writer = csv.writer(outcsv, quoting=csv.QUOTE_ALL)
                        for row in rows:
                                writer.writerow(row)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Convert sqldump to csv')

    parser.add_argument('sql_filepath', action="store", type=str)
    parser.add_argument('output_dir', action="store", default='.', type=str)

    args = parser.parse_args()

    file_path = args.sql_filepath
    out_dir = args.output_dir if args.output_dir.endswith('/') else args.output_dir + '/'

    main(file_path, out_dir)
