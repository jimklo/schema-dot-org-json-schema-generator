#! /usr/bin/env python

   # Copyright 2013 SRI International

   # Licensed under the Apache License, Version 2.0 (the "License");
   # you may not use this file except in compliance with the License.
   # You may obtain a copy of the License at

   #     http://www.apache.org/licenses/LICENSE-2.0

   # Unless required by applicable law or agreed to in writing, software
   # distributed under the License is distributed on an "AS IS" BASIS,
   # WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   # See the License for the specific language governing permissions and
   # limitations under the License.

import argparse, urllib2, json, pprint, jsonschema, jsonpatch

# all_schema_org = json.load(urllib2.urlopen("http://schema.rdfs.org/all.json"))

all_schema_org = json.load(open("schemas/schema-rdfs-org.json"))

lrmi_mixin = json.load(open("schemas/lrmi-json-microdata-mixin.json"))

log = None

json_schema = json.load(open("schemas/microdata-json-schema.json"))


def get_prop_schema(prop_name):
    prop_def = all_schema_org["properties"][prop_name]
    prop_schema = {
        "title": prop_def["label"],
        "description": prop_def["comment_plain"],
        "type": "array",
        "items": {},
        "additionalItems": True
    }

    # if prop_name == "acceptedPaymentMethod":
    #     import pdb; pdb.set_trace()

    prop_schema["items"] =  get_schemas_for_ranges(prop_def["ranges"]) 
    return prop_def["id"], prop_schema

def get_schemas_for_ranges(ranges=[]):
    schemas = []
    instances = []
    for r in ranges:
        if r not in schemas:
            schemas.append(r)
            if r in all_schema_org["types"]:
                subids, subinstances = find_subids(all_schema_org["types"][r], [])
                if len(subinstances)>0:
                    for inst in subinstances:
                        if inst not in instances:
                            instances.append(inst)
                else:
                    for i in subids:
                        if i not in schemas:
                            schemas.append(i)
    
    result = []
    
    if len(instances)>0:
        result.append({
            "enum": map("http://schema.org/{0}".format, instances)   
        })
    if len(schemas)>0:
       result += map(lambda x: { "$ref": "#/definitions/{0}".format(x)}, schemas)

    if len(result) == 1:
        return result[0]
    else:
        return {
            "oneOf": result
        }
    

def unique(seq):
    return {}.fromkeys(seq).keys()

def find_subids(type_def, type_list=[]):

    instance_list=[]

    # if type_def["id"] == "Thing":
    #     import pdb; pdb.set_trace()


    try: 

        if len(type_def["instances"]) > 0:
            instance_list += type_def["instances"]
            return [], instance_list
    except:
        pass


    if "id" in type_def and type_def["id"] not in type_list:
        type_list.append(type_def["id"])

    try:
        for subtype in type_def["subtypes"]:
            subtype_def = all_schema_org["types"][subtype]
            type_list, new_instance_list = find_subids(subtype_def, type_list)
            instance_list += new_instance_list

    except:
        pass

    return type_list, unique(instance_list)

def find_subtypes(type_def, type_list=[]):
    if "url" in type_def and type_def["url"] not in type_list:
        type_list.append(type_def["url"])

    try:
        for subtype in type_def["subtypes"]:
            subtype_def = all_schema_org["types"][subtype]
            type_list = find_subtypes(subtype_def, type_list)
    except:
        pass

    return type_list

def find_subtype_ids(type_def, type_list=[]):
    if "id" in type_def and type_def["id"] not in type_list:
        type_list.append(type_def["id"])

    try:
        for subtype in type_def["subtypes"]:
            subtype_def = all_schema_org["types"][subtype]
            type_list = find_subtype_ids(subtype_def, type_list)
    except:
        pass

    return type_list





def get_type_schema(type_def):
    type_schema = {
        "title": type_def["label"],
        "description": type_def["comment_plain"],
        "allOf": []
            # [ { "$ref": "#/definitions/microdata" } ]
        
    }
    
    propset_name = "propset_{0}".format(type_def["id"])
    this_propset = {}
    for spec_prop in type_def["specific_properties"]:
        prop_name, prop_def = get_prop_schema(spec_prop)

        this_propset[prop_name] = prop_def

    json_schema["definitions"][propset_name] = {
        "properties": this_propset
    }


    if "instances" in type_def:
        type_inst = {
            "enum":  map(lambda x: "http://schema.org/{0}".format(x), type_def["instances"]) 
        }

        type_schema.update(type_inst)
        del type_schema["allOf"]
        
    else:
        this_schema = {
            "properties": {
                "id": { "type": "string" },
                "type": {
                    "enum": [[type_def["url"]]]
                },
                "properties": { },
                
            },
            "required": ["type", "properties"],
            "additionalProperties": False
        }
        this_schema["properties"]["properties"]["allOf"] = []
        

        if len(type_def["properties"]) > 0:
            this_schema["properties"]["properties"]["additionalProperties"] = False
            # this_schema["properties"]["properties"]["properties"] = {}
            patterns = "^({0})$".format("|".join(type_def["properties"]))
            
            this_schema["properties"]["properties"]["patternProperties"] = {
                patterns : {
                    "type": "array",
                    "minItems": 1,
                    "items": {
                        "anyOf":[
                            { "$ref": "#/definitions/microdata" },
                            { "type": "string" }
                        ]
                    },
                    "additionalItems": True
                }
            }

        # if len(type_def["specific_properties"]) > 0 or len(type_def["supertypes"]) > 0:
        #     this_schema["properties"]["properties"]["anyOf"] = []

       
            # this_schema["properties"]["properties"]["properties"][prop_name] = prop_def

        if len(this_propset.keys()) >= 0:
            
            this_schema["properties"]["properties"]["allOf"].append({"$ref": "#/definitions/{0}".format(propset_name)})

        if len(type_def["supertypes"]) > 0:
            this_schema["properties"]["properties"]["allOf"] += map(lambda x: { "$ref": "#/definitions/propset_{0}".format(x)}, type_def["supertypes"])


        type_schema.update(this_schema)
        del type_schema["allOf"]
        # type_schema["allOf"].append(this_schema)


    # if len(type_def["supertypes"]) > 0:
    #     type_schema["anyOf"] = map(lambda x: { "$ref": "#/definitions/{0}".format(x)}, type_def["supertypes"])

    return type_schema


def init():
    global json_schema, log
    log = open("lrmi.json", "w")
    json_schema["properties"]["items"]["items"]["allOf"][2]["anyOf"] = []
    microdata = json_schema["definitions"]["microdata"]
    json_schema["definitions"] = { "microdata": microdata }

def processDatatypes():
    for type_name, type_def in all_schema_org["datatypes"].items():
        if type_name not in json_schema["definitions"]:
            type_schema = get_type_schema(type_def)
            json_schema["definitions"][type_name] = type_schema

def processTypes():
    for type_name, type_def in all_schema_org["types"].items():
        type_schema = get_type_schema(type_def)     
        json_schema["definitions"][type_name] = type_schema
        # if "enum" not in type_schema:
        #     json_schema["properties"]["items"]["additionalItems"]["allOf"][0]["oneOf"].append(
        #         {
        #             "$ref": "#/definitions/{0}".format(type_name)
        #         }
        #     )
        
        if type_name in ["CreativeWork", "EducationalAudience", "Person", "Organization", "Event"]:
            for type_id in find_subtype_ids(type_def, []):
                json_schema["properties"]["items"]["items"]["allOf"][2]["anyOf"].append(
                    {
                        "$ref": "#/definitions/{0}".format(type_id)
                    }
                )

# def mixin():
#     for schema_ref in lrmi_mixin["properties"]["items"]["items"]["oneOf"]:
#         if schema_ref not in json_schema["properties"]["items"]["items"]["anyOf"]:
#             json_schema["properties"]["items"]["items"]["anyOf"].append(schema_ref)

#     for schema_name, schema_def in lrmi_mixin["definitions"].items():
#         if schema_name in json_schema["definitions"]:
#             for mixin_name, mixin_def in schema_def["properties"]["properties"]["properties"].items():
#                 if mixin_name not in json_schema["definitions"][schema_name]["properties"]["properties"]["properties"]:
#                     json_schema["definitions"][schema_name]["properties"]["properties"]["properties"].update({ mixin_name: mixin_def })
#         else:
#             json_schema["definitions"].update( { schema_name: schema_def })

def patch():
    global json_schema
    json_schema = jsonpatch.apply_patch(json_schema, lrmi_mixin)


def validateTests(schema):
    validate(jsonschema.Draft4Validator.META_SCHEMA, "./lrmi.json")

    validate(schema, "./data/sample_data1.json")
    # import pdb; pdb.set_trace()
    validate(schema, "./data/sample_data2.json")
    validate(schema, "./data/sample_data3.json")
    validate(schema, "./data/sample_data4.json")
    validate(schema, "./data/sample_data5.json")
    validate(schema, "./data/sample_data6.json")
    validate(schema, "./data/sample_data7.json")

def validate(schema, instance_file):

    print "\n\n\n\n##### validating instance from {0} ######".format(instance_file)
    validator = jsonschema.Draft4Validator(schema, format_checker=jsonschema.FormatChecker())

    with open(instance_file) as f:
        inst = json.load(f)
        print json.dumps(inst)
        errors = sorted(validator.iter_errors(inst), key=lambda e: e.path)
        for idx, err in enumerate(errors, 1):
            print "{0}. {1}\n".format(idx, err)
        # for idx, err in enumerate(validator.iter_errors(inst), 1):
        #     print "{0}. {1}\n".format(idx, pprint.pformat(err))


def main():
    validator = jsonschema.Draft4Validator(jsonschema.Draft4Validator.META_SCHEMA, format_checker=jsonschema.FormatChecker())

    init()

    print "##### initial #######"
    for err in validator.iter_errors(json_schema):
        pprint.pprint(err)

    processDatatypes()

    # print "##### base datatypes #######"
    # for err in validator.iter_errors(json_schema):
    #     pprint.pprint(err)


    processTypes()
    patch()

    log.write(json.dumps(json_schema, indent=4))
    log.close()

    print "##### done #######"

 
    validateTests(json_schema)
        
    # jsonschema.Draft4Validator.check_schema(json_schema)


def just_valid():
    with open("lrmi.json") as f:
        schema = json.load(f)
        validateTests(schema)


# pprint.pprint(all_schema_org)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--regen', '-r', help="regen schema", action="store_true", default=False)
    parser.add_argument('--test', '-t', help="test schema", action="store_true", default=False)
    args = parser.parse_args()
    if args.regen and not args.test:
        main()
    else:
        just_valid()

    # main()
    # print(find_subtypes(all_schema_org["types"]["CreativeWork"]))



