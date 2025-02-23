"""
Imports the data from the CSV file generated by Qualtrics.
Any entires already in the database are ignored during the import.
"""
import sys
import csv
import records
import time

# Be sure to check the Qualtrics forms for what these values should be.
JUDGE_ROLE_NUM = '1'
"""A string that represents the judge role in the volunteer form's CSV file."""
MENTOR_ROLE_NUM = '2'
"""A string that represents the mentor role in the volunteer form's CSV file."""

# If you need to import more data, modify this to include the additional attributes you need.
DATA_ATTR = {
    'First Name':'first_name'
}
"""
A dictionary of attribute names that should be searched for and included as non-essential data.
</br>
The keys of this dictionary are the attribute names used in the CSV file.
</br>
The values of this dictionary are the attribute names used elsewhere in the bot code.
"""

# Variable to keep track of stats for report at the end.
num_duplicates = 0
num_error = 0
num_unfinished = 0
num_entries = 0
start_time = time.time()

with open(sys.argv[1], 'r') as csv_file:
    # Try to open the provided file name.
    try:
        reader = csv.DictReader(csv_file, delimiter=',')
    except:
        raise BaseException('Cannot read/import CSV file. Check format and resubmit.')

    # Verify that the file has all the attributes we need.
    attributes = set(reader.fieldnames)
    try:
        attributes.remove('Progress')
        attributes.remove('Email')
    except:
        raise ValueError('CSV file missing required attributes. Check file contents and resubmit.')

    # Check if we are importing the participant or volunteer form.
    isParticipant = False
    try:
        attributes.remove('Roles')
    except:
        isParticipant = True

    # For each entry in the CSV file...
    for entry in reader:
        num_entries = num_entries + 1

        # Check that the entry is for a completed response.
        if entry['Progress'] != '100':
            num_unfinished = num_unfinished + 1
            continue

        # Check for and store the entry's email.
        if entry['Email'] == '':
            num_error = num_error + 1
            continue
        email = entry['Email'].replace(' ', '')

        # Check for and store the entry's roles.
        roles = []
        if isParticipant:
            roles.append('participant')
        else:
            # If the roles attribute exists but is blank, skip this entry.
            if entry['Roles'] == '':
                num_error = num_error + 1
                continue
            # Add appropriate roles for the volunteer form.
            if entry['Roles'].find(JUDGE_ROLE_NUM) != -1:
                roles.append('judge')
            if entry['Roles'].find(MENTOR_ROLE_NUM) != -1:
                roles.append('mentor')

        # Check for and store all non-essential data.
        data = {}
        for attribute in DATA_ATTR.keys():
            try:
                data[DATA_ATTR[attribute]] = entry[attribute]
            except:
                pass

        # Add this entry's data to the database if it is not a duplicate.
        if records.registered_user_exists(email):
            # Get the existing version of this entry.
            old_entry = records.get_registered_user(email)
            is_duplicate = old_entry['roles'] == roles

            # Check all attributes in DATA_ATTR.
            for attribute in DATA_ATTR.values():
                try:
                    is_duplicate = is_duplicate and old_entry['data'][attribute] == data[attribute]
                except:
                    # If a key does not exist, then an attribute was added to DATA_ATTR.
                    is_duplicate = False
                    break

            # Check all attributes in the old entry's data JSON.
            for attribute in old_entry['data'].keys():
                try:
                    is_duplicate = is_duplicate and old_entry['data'][attribute] == data[attribute]
                except:
                    # If a key does not exist, then an attribute was removed from DATA_ATTR.
                    is_duplicate = False
                    break

            # If this entry is not a duplicate, add it.
            if not is_duplicate:
                records.add_registered_user(email, roles, data)
            else:
                num_duplicates = num_duplicates + 1
        else:
            # If this entry is not in the database, add it.
            records.add_registered_user(email, roles, data)

# There are essentially three header rows in the CSV file generated by Qualtrics.
# One header row is the actual header row, and the other two rows are treated as entries
# by the CSV reader. As such, subtract two from the relevant totals.
num_entries = num_entries - 2
num_unfinished = num_unfinished - 2

# Output statistics to help with any troubleshooting that may come up.
print(f'Finished importing {sys.argv[1]}')
print(f'Processing time: {time.time() - start_time:.3f} seconds')
print(f'Total number of entries processed: {num_entries}')
print(f'-----------------------------------------')
print(f'Number of entries added to database:', end=' ')
print(f'{num_entries - num_duplicates - num_error - num_unfinished} out of {num_entries}')
print(f'Number of duplicate entries: {num_duplicates} out of {num_entries}')
print(f'Number of entries with incomplete information: {num_error} out of {num_entries}')
print(f'Number of unfinished entries: {num_unfinished} out of {num_entries}')
