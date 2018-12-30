# -*- coding: utf-8 -*-
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

def get_lists(file_name):
    with open(file_name) as f:
        flattened_lists = {}
        config_jason = f.read()
        try:
            parsed_json = json.loads(config_jason.replace('\n', ''))
            for r in parsed_json["optionLists"]:
                option_list = parsed_json["optionLists"][r]
                flattened_lists[r] = {}
                if 'messages' in option_list and not 'Unknown' in option_list['messages']:
                    for message in option_list['messages']:
                        flattened_lists[r][message] = option_list['messages'][message]["defaultMessage"]
                elif 'values' in option_list:
                    for t in option_list['values']:
                        flattened_lists[r][t] = t
        except:
            raise
            print 'Error loading JSON config file'

    return flattened_lists


if __name__ == "__main__":
    static_lists = get_lists(sys.argv[1])

    for list in sorted(static_lists):
        print list
        for key in sorted(static_lists[list]):
            print '   %-25s %s' % (key.encode('utf-8'), static_lists[list][key].encode('utf-8'))
