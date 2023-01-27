import json
import toml

# with open("credentials.json", "r") as json_file:
#     json_data = json.load(json_file)

# with open("creds.toml", "w") as toml_file:
#     toml.dump(json_data, toml_file)

with open("creds.toml", "r") as toml_file:
    data = toml.load(toml_file)
    print(data['credentials'])
