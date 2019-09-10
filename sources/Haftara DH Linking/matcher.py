#encoding=utf-8
import django
django.setup()
from sefaria.model import *
from data_utilities.dibur_hamatchil_matcher import *
from sefaria.system.database import db
from sources.functions import *
import json
import re
with open("parashot-haftarot.json") as f:
    parasha_to_haftara = json.load(f)

def base_tokenizer(str):
    return str.split()

def dh(str):
    str = str.replace("<b>", "").replace("</b>", "")
    str = re.sub(u"^([\(\)\.\S]{1,3}\s)", u"", str)


    if u"וכו'" in str:
        result = str.split(u"וכו'")[0]
    elif u"וגו'" in str:
        result = str.split(u"וגו'")[0]
    elif "." in u" ".join(str.split()[0:10]):
        result = str.split(".")[0]
    else:
        result = u" ".join(str.split()[0:8])
    return result.strip()


titles = ["Nachal Sorek", "Tzaverei Shalal"]
links = {"Nachal Sorek": [], "Tzaverei Shalal": []}
for title in titles:
    all_refs = library.get_index(title).all_section_refs() if title == "Nachal Sorek" else library.get_index(title).all_segment_refs()
    for ref in all_refs:
        if ref.is_segment_level() and len(ref.sections) > 1 and ref.sections[1] > 1:
            continue
        haftarah_name = ref.normal().replace("Haftarah of ", "").replace("Haftarah for the ", "")
        haftarah_name = haftarah_name.replace("{}, ".format(title), "")
        haftarah_name = re.sub(" [\:\d]+$", "", haftarah_name)
        try:
            haftarah_dict = parasha_to_haftara[haftarah_name]
        except KeyError as e:
            print e.message
            continue
        haftarah_refs = haftarah_dict["sephardi"] if "sephardi" in haftarah_dict.keys() else haftarah_dict["ashkenazi"]
        for haftarah_ref in haftarah_refs:
            haftarah_ref = Ref(haftarah_ref)
            haftarah_tc = TextChunk(haftarah_ref, lang='he', vtitle="Tanach with Text Only")
            comments = ref.text('he').text if title == "Nachal Sorek" else [ref.text('he').text]
            results = match_ref(haftarah_tc, comments, base_tokenizer=base_tokenizer, dh_extract_method=dh)
            for n, result in enumerate(results["matches"]):
                if result:
                    if title != "Nachal Sorek":
                        comm_ref = Ref(ref.normal().rsplit(":", 1)[0])
                        comm_ref = comm_ref.as_ranged_segment_ref().normal()
                    else:
                        comm_ref = "{} {}".format(ref, n+1)

                    links[title].append({"refs": [result.normal(), comm_ref], "generated_by": "haftara_matcher", "auto": True,
                                  "type": "Commentary"})


post_link(links["Nachal Sorek"], server="http://ste.sandbox.sefaria.org")
post_link(links["Tzaverei Shalal"], server="http://ste.sandbox.sefaria.org")

#for l in links:
#    print l["refs"]
print links.keys()
print len(links[links.keys()[0]])
print len(links[links.keys()[1]])