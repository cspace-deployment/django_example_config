import json
import sys

'''
Option lists resemble the following:

    "optionLists": {
        "accountStatuses": {
            "messages": {
                "active": {
                    "defaultMessage": "active",
                    "id": "option.accountStatuses.active"
                },
                "inactive": {
                    "defaultMessage": "inactive",
                    "id": "option.accountStatuses.inactive"
                }
            },
            "values": [
                "active",
                "inactive"
            ]
        },
'''


with open(sys.argv[1]) as f:
    flattened_lists = {}
    config_jason = f.read()
    try:
        parsed_json = json.loads(config_jason.replace('\n', ''))
        for r in parsed_json["optionLists"]:
            option_list = parsed_json["optionLists"][r]
            flattened_lists[r] = []
            if 'messages' in option_list and not 'Unknown' in option_list['messages']:
                for message in option_list['messages']:
                    flattened_lists[r].append((message, option_list['messages'][message]["defaultMessage"]))
            elif 'values' in option_list:
                tuple_list = [(t, t) for t in option_list['values']]
                flattened_lists[r] = tuple_list
    except:
        raise
        print 'Error loading JSON config file'

for list in sorted(flattened_lists):
    print list
    for pair in sorted(flattened_lists[list]):
        print '   ', pair