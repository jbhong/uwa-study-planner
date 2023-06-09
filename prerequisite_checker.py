"""
    program to check the prerequisite tree for UWA units and degrees
    Written by : Jin Hong
    date       : 15 March 2023
"""

import copy
import requests
from bs4 import BeautifulSoup
import pickle
import pathlib
import re
from itertools import product
import sys

# UNIT_PATH = "./uwa-study-planner/units/"
# COURSE_PATH = "./uwa-study-planner/courses/"
UNIT_PATH = "./units/"
COURSE_PATH = "./courses/"
HONOURS = ["CITS4010", "CITS4011"]

class Unit:
    URL = "https://handbooks.uwa.edu.au/unitdetails?code="
    PREREQ = "./prereq_list.txt"
    
    def __init__(self, ucode="", text=[], get_text=True) -> None:
        self.code = ucode
        if get_text:
            text = self.get_text()
            if text == []:
                #print("There was no text data provided, check your url...")
                return
        self.text = text
        self.title = text[text.index("UWA Handbook 2023") + 1]

        self.description = ""
        i = text.index("Description") + 1
        j = [text.index(j) for j in text if j.startswith("Credit")][0]
        for k in range(i, j):
            self.description += text[k].strip() + "\n"
        
        self.credit = int(text[j].strip("Credit").strip("points").strip())
        
        self.offering = "NA"
        i = [text.index(j) for j in text if j.startswith("Offering")][0]
        
        try:
            j = [text.index(j) for j in text if j.startswith("Details for undergraduate courses")][0]
        except:
            j = text.index("Outcomes")

        for k in range(i, j):
            self.offering += text[k]
        rows = self.offering.split("Semester")

        self.offer = []
        self.semester = set()
        for row in rows:
            if "Not available" in row:
                self.offer = "Not available"
            elif "1" in row:
                self.semester.add(1)
                if "Face" in row:
                    if "UWA (Perth)" in row:
                        self.offer.append(("Semester 1", "UWA (Perth)", "Face to face"))
                    elif "Albany" in row:
                        self.offer.append(("Semester 1", "Albany", "Face to face"))
                elif "Restricted" in row:
                    if "UWA (Perth)" in row:
                        self.offer.append(("Semester 1", "UWA (Perth)", "Online Restricted"))
                    elif "Albany" in row:
                        self.offer.append(("Semester 1", "Albany", "Online Restricted"))
                elif "Online timetabled" in row:
                    if "UWA (Perth)" in row:
                        self.offer.append(("Semester 1", "UWA (Perth)", "Online timetabled"))
                    elif "Albany" in row:
                        self.offer.append(("Semester 1", "Albany", "Online timetabled"))
                    else:
                        self.offer.append(("Semester 1", "Online", "Online timetabled"))
                elif "Online" in row:
                    if "UWA (Perth)" in row:
                        self.offer.append(("Semester 1", "UWA (Perth)", "Online"))
                    elif "Albany" in row:
                        self.offer.append(("Semester 1", "Albany", "Online"))
            elif "2" in row:
                self.semester.add(2)
                if "Face" in row:
                    if "UWA (Perth)" in row:
                        self.offer.append(("Semester 2", "UWA (Perth)", "Face to face"))
                    elif "Albany" in row:
                        self.offer.append(("Semester 2", "Albany", "Face to face"))
                elif "Restricted" in row:
                    if "UWA (Perth)" in row:
                        self.offer.append(("Semester 2", "UWA (Perth)", "Online Restricted"))
                    elif "Albany" in row:
                        self.offer.append(("Semester 2", "Albany", "Online Restricted"))
                elif "Online timetabled" in row:
                    if "UWA (Perth)" in row:
                        self.offer.append(("Semester 2", "UWA (Perth)", "Online timetabled"))
                    elif "Albany" in row:
                        self.offer.append(("Semester 2", "Albany", "Online timetabled"))
                    else:
                        self.offer.append(("Semester 2", "Online", "Online timetabled"))
                elif "Online" in row:
                    if "UWA (Perth)" in row:
                        self.offer.append(("Semester 2", "UWA (Perth)", "Online"))
                    elif "Albany" in row:
                        self.offer.append(("Semester 2", "Albany", "Online"))


        self.ugdetails = "Check the handbook"
        i = [text.index(j) for j in text if j.startswith("Offering")][0]
        j = text.index("Outcomes")
        while not text[i].startswith("Details for undergraduate") and i < j:
            i += 1
        if text[i].startswith("Details for undergraduate"):
            text[i] = text[i].replace("Details for undergraduate courses", "")

            self.ugdetails = ""
            for k in range(i, j):
                self.ugdetails += text[k].replace("Level ", " Level ").strip() + "\n"
        self.ugdetails = self.ugdetails.strip()

        self.outcomes = ""
        i = text.index("Outcomes") + 1
        j = [text.index(j) for j in text if j.startswith("Assessment")][0]
        for k in range(i, j):
            self.outcomes += text[k] + "\n"

        try:
            self.coordinator = text[text.index("Unit Coordinator(s)") + 1]
        except:
            print(f"No coordinator in this unit: {self.code}")
            self.coordinator = ""
        try:
            prereq = text[text.index("Prerequisites") + 1].split("or ")
            prereq = " or ".join([row.strip() for row in prereq]).split("and ")
            prereq = " and ".join([row.strip() for row in prereq])
            prereq = prereq.replace("Enrolment in", "Enrolment in ")
            prereq = prereq.replace("Programming and System", "Programming & System")
            prereq = prereq.replace("FoundationsandCITS1401", "Foundations and CITS1401")
            prereq = prereq.replace("Java andM", "Java and M")
            prereq = prereq.replace("Bachel or", "Bachelor")
            prereq = prereq.replace(" in   in the", " in the ")
            prereq = prereq.replace("specialisationorthe", "specialisation or the")
            prereq = prereq.replace("IntelligenceorBachelor", "Intelligence or Bachelor")
            prereq = prereq.replace("in in", "in")
            prereq = prereq.replace("the the", "the")
            prereq = prereq.replace(" inthe ", " in the ")
            prereq = prereq.replace("Scienceorthe", "Science or the")
            prereq = prereq.replace(" maj or ", " major")
            prereq = prereq.replace("majorand", "major and")
            prereq = prereq.replace("pri or", "prior")
            prereq = prereq.replace(" including", " including ")
            prereq = prereq.replace("of96", "of 96")
            prereq = prereq.replace("  ", " ")
            if " f or " in prereq:
                prereq = prereq.replace(" f or ", " for ")
            self.prereq = prereq
        except:
            print(f"No prerequisites in this unit: {self.code}")
            self.prereq = ""
        
        self.prereqlist = []
        self.update_prereqlist()


        try:
            incomp = text[text.index("Incompatibility") + 1].split("or ")
            incomp = " or ".join([row.strip() for row in incomp]).split("and ")
            incomp = " and ".join([row.strip() for row in incomp])
            if " f or " in incomp:
                incomp = incomp.replace(" f or ", " for ")
            incomp = incomp.replace("Enrolment in", "Enrolment in ")
            incomp = incomp.replace("FoundationsandCITS1401", "Foundations and CITS1401")
            self.incompatibility = incomp
        except:
            print(f"No incompatibility in this unit: {self.code}")
            self.incompatibility = ""

    def __str__(self):
        offer = f"\n{'':22}".join([f"{i} | {j:12} | {k}" for (i, j, k) in self.offer])
        return (f"{'Unit Code':20}: {self.code}\n"
                f"{'Unit Title':20}: {self.title}\n"
                f"{'Unit Credit':20}: {self.credit}\n"
                f"{'Unit Offering':20}: {offer}\n"
                f"{'Unit Semesters':20}: {sorted(self.semester)}\n"
                f"{'Unit UG details':20}: {self.ugdetails}\n"
                f"{'Unit Coordinator':20}: {self.coordinator}\n"
                f"{'Unit Prerequisites':20}: {self.prereq}\n"
                f"{'Unit Incompatibility':20}: {self.incompatibility}\n"
                f"\n"
                f"{'Unit Description':20}: {self.description}\n"
                f"{'Unit Outcomes':20}: {self.outcomes}"
                #f"{self.offering}"
                )


    def update_values(self):
        """call all the update functions when saving unit"""
        self.update_prereqlist()

    def update_prereqlist(self) -> None:
        """update the prereq list in case modified"""
        # do some prep work
        if "Data Structures and Algorithms" in self.prereq:
            self.prereq = self.prereq.replace("Data Structures and Algorithms",
                                "Data Structures & Algorithms")
        if "Theory and Methods" in self.prereq:
            self.prereq = self.prereq.replace("Theory and Methods",
                                "Theory & Methods")
        if "Analysis and Visualisation" in self.prereq:
            self.prereq = self.prereq.replace("Analysis and Visualisation",
                                "Analysis & Visualisation")
        if "Intelligence and Adaptive" in self.prereq:
            self.prereq = self.prereq.replace("Intelligence and Adaptive",
                                "Intelligence & Adaptive")  
        if "Mobile and Wireless" in self.prereq:
            self.prereq = self.prereq.replace("Mobile and Wireless",
                                "Mobile & Wireless")  
        if "Tools and Scripting" in self.prereq:
             self.prereq = self.prereq.replace("Tools and Scripting",
                                "Tools & Scripting")  
        if "Testing and Quality" in self.prereq:
             self.prereq = self.prereq.replace("Testing and Quality",
                                "Testing & Quality")  
        if "6 points of programming" in self.prereq:
            self.prereq = self.prereq.replace("6 points of programming",
                                "CITS1401 or CITX1401")
        elif "12 points of programming" in self.prereq:
            self.prereq = self.prereq.replace("12 points of programming",
                                "CITS2002 or CITS2005")

        #list of all unit codes in prereq and "or" and "and"
        matches = "".join(self.match_code(self.prereq)).strip("andor ")
        #print("MATCHES", matches)
        and_groups = [code for code in matches.split(' and ') if code.strip("andor ")]
        # Split each 'and' group by 'or' separator
        or_groups = [[code for code in group.split(' or ') if code.strip("andor ")] 
                     for group in and_groups]

        # Generate all possible combinations of subjects
        self.prereqlist = [list(pair) for pair in list(product(*or_groups)) if pair]        

    def match_code(self, text):
        pattern = r'\b[a-zA-Z]{4}\d{4}\b|\b and \b|\b or \b'
        matches = re.findall(pattern, text)
        return matches  

    def save(self, fname="", update=True):
        """saves the unit file"""
        if update:
            self.update_values()
        fname = self.code if fname == "" else fname
        with open(UNIT_PATH + fname, 'wb') as f:
            pickle.dump(self, f)
    

    def load(self, code):
        """returns the saved unit file"""
        try:
            with open(UNIT_PATH + code, 'rb') as f:
                return pickle.load(f)
        except FileNotFoundError:
            print(f"UnitClassError: file {code} doesn't exist... I'll get it from the handbook and make it...")
            try:
                self.code = code
                text = self.get_text()
                unit = Unit(code, text, False)
                unit.save()
                return unit
            except:
                print(f"Could not create unit: {code}")


    def update(self):
        """updates the content with a fresh pull from the handbook"""
        try:
            text = self.get_text()
            unit = Unit(self.code, text, False)
            unit.save()
            return unit
        except:
            print(f"Could not create unit: {self.code}")
    
    def delete(self):
        """checks the handbook online and deletes the unit file if not in the handbook"""
        if requests.get(Unit.URL + self.code).status_code != 200:
            pathlib.Path(UNIT_PATH + self.code).unlink()

    def get_text(self):
        """returns the text from the web"""
        if len(self.code) > 0:
            response = requests.get(Unit.URL + self.code)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "html.parser")
                return [s.strip() for s in soup.get_text().splitlines() if s.strip()]
            else:
                print(f"the url for unit, {self.code}, doesn't exist... try again...")
        return []


class UnitList:
    URL = 'https://handbooks.uwa.edu.au/unitdetails?code='

    def __init__(self, fname="", ulist=[]) -> None:
        self.fname = fname
        self.ulist = ulist
        self.units = self.get_unit_list() #this is a dictionary of code:Unit
        
    def __contains__(self, code):
        return code in self.units.keys()

    def __str__(self):
        out = ""
        for unit in list(self.units.keys()):
            out += f"{unit}, "
        return out.strip(", ")


    def __getitem__(self, code):
        return self.units[code]

    def get_unit_list_helper(self, codes):
        """get units helper"""
        units = {}
        for code in codes:
            success = False
            try:
                if type(code) == str:
                    unit = Unit().load(code)
                    success = True
            except FileNotFoundError:
                print(f"the unit, {code}, doesn't exist, so making it...")
                unit = Unit(code)
            except:
                print(f"could not make the unit, {code}... skipping...")
                continue
            if success:
                units[code] = unit
        return units


    def get_unit_list(self):
        """returns the list of unit code"""
        if len(self.fname) > 0:
            try:
                with open(self.fname) as f:
                    codes = [code.strip() for code in f.readlines()]
                    return self.get_unit_list_helper(codes)
            except:
                print(f"the unit list: {self.fname}, doesn't exist... try making it...")
        elif len(self.ulist) > 0:
            return self.get_unit_list_helper(self.ulist)
        return {}


    def update_unit_list(self, unit) -> None:
        """updates the unit list if missing"""
        if unit not in self.units:
            self.units[unit.code] = unit
            with open(self.fname, 'w') as f:
                for code in sorted(list(self.units.keys())):
                    f.write(code + "\n")

    def set_fname(self, fname):
        """set fname"""
        self.fname = fname

    def save(self, fname=""):
        """save the current list of units to file fname"""
        fname = self.fname if len(fname) == 0 else fname
        output = "*" * 30
        output += "\n"
        for _, unit in sorted(self.units.items()):
            output += str(unit)
            output += "\n"
            output += "*" * 30
            output += "\n"
            
        with open(fname, "w") as f:
            f.write(output)

    def remove_none_units(self) -> None:
        """go through the unit list and remove if not found in the handbook online"""
        codes = set([code for code in self.units
                        if requests.get(UnitList.URL + code).status_code != 200])
        for code in codes:
            del(self.units[code])
            pathlib.Path(UNIT_PATH + code).unlink()

        with open(self.fname, 'w') as f:
            for code in sorted(list(self.units)):
                f.write(code + "\n")


    def get_next_unit_code(self, ucode, bound=90, start='A') -> str:
        """ ucode is the unit code, which is always 4 letters and 4 digits
            A-Z ord is 65 to 90.
            0-0 ord is 48 to 57.
            Call with bound 90 and start 'A' for letter code
            Call with bound 57 and start '0' for number code
        """
        ucode = list(ucode)
        char_ind = 3          #start with the last letter
        
        #past Z so increment the next letter
        while char_ind >= 0:
            if ord(ucode[char_ind]) + 1 > bound:
                ucode[char_ind] = start 
            else:
                ucode[char_ind] = chr(ord(ucode[char_ind]) + 1)
                char_ind = 0
            char_ind -= 1

        return ''.join(ucode)       

    def is_code(self, ucode):
        """check if ucode is actually code"""
        return (len(ucode) == 8 and 
                ucode[4:].isnumeric() and
                ucode[:4].isalpha())


    def find_units(self, ucode="", stop="6000") -> list:
        """ Try entire possible unit codes and retrieve all units.
            This is to discover any new units.
            if ucode is provided, only that code will be checked.
            This is VERY slow.
        """
        #some starting unit code
        if ucode == "":
            uletter = "AAAA" 
            unumber = "1000"
        elif self.is_code(ucode):
            uletter = ucode[:4]
            unumber = ucode[4:]
        else:
            print(f"the code, {ucode}, is not valid unit code... exiting...")
            return
 
        while (uletter + unumber != "ZZZZ" + stop):
            print(f"Checking: {uletter + unumber}")
            if (uletter + unumber) not in self.units:
                unit = Unit(uletter + unumber)
                if len(unit.text) > 0:
                    print(f"Found unit: {unit.code}!")

                    #update the unit list
                    self.update_unit_list(unit)

                    #save the new unit object
                    unit.save()
            else:
                print(f"{uletter + unumber} already in the list... skipping...")
            if unumber < stop:
                unumber = self.get_next_unit_code(unumber, 57, "0")
            elif (unumber == stop):
                uletter = self.get_next_unit_code(uletter, 90, "A")
                unumber = "1000"
                if (len(ucode) > 0): #finished for the given unit code
                    return
        return



    def save_unit(self, unit):
        """saves the unit object"""
        with open(UNIT_PATH + unit.code, 'wb') as f:
            pickle.dump(unit, f)


class Course:
    def __init__(self, url=None) -> None:
        self.url = url
        self.text = self.get_text()
        self.title = ""
        self.conversion = {}
        self.bridging = {}
        self.core = {}
        self.option = {}
        self.unitlist = UnitList()
        self.study_plan_s1 = {"Y1S1" : [], "Y1S2" : [], "Y2S1" : [], "Y2S2" : [], "Y3S1" : [], "Y3S2" : [], "Y4S1" : [], "Y4S2" : []}
        self.study_plan_s2 = {"Y1S2" : [], "Y1S1" : [], "Y2S2" : [], "Y2S1" : [], "Y3S2" : [], "Y3S1" : [], "Y4S2" : [], "Y4S1" : []}
        if url and len(self.text) > 0:
            self.title = self.text.split(":")[0].strip()
            self.conversion, self.bridging, self.core, self.option = self.find_units()
            units = []
            [units.extend(value) for value in self.conversion.values()]
            [units.extend(value) for value in self.bridging.values()]
            [units.extend(value) for value in self.core.values()]
            for values in self.option.values():
                if len(values) > 0:
                    for value in values:
                        units.extend(value[1:])
            self.unitlist = UnitList(ulist=units)
        # if len(self.core) > 0:
        #     self.get_study_plan()
                    
    def __str__(self):
        result = "*" * 20 + "\n"
        for level in range(0, 6):
            if level in self.conversion:
                result += f"Conversion units:\n"
                for unit in self.conversion[level]:
                    result += f"{unit}\n"
            if level in self.bridging:
                result += f"Bridging units:\n"
                for unit in self.bridging[level]:
                    result += f"{unit}\n"
            if level in self.core:
                result += f"Level {level} Core:\n"
                for unit in self.core[level]:
                    result += f"{unit}\n"
            if level in self.option:
                if len(self.option[level]) > 0:
                    result += f"\nLevel {level} Option:\n"
                for units in self.option[level]:
                    points = units[0]
                    units.pop(0)
                    result += f"Take unit(s) to the value of {points} points.\n"
                    for unit in units:
                        result += f"{unit}\n"
            result += "\n" + "*" * 20 + "\n"
        return result.strip() 

    def get_text(self):
        """fetch the text data from the url"""
        if self.url is not None:
            response = requests.get(self.url)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "html.parser")
                #return [s.strip() for s in soup.get_text().splitlines() if s.strip()]
                # below two lines replace the one above
                text = soup.get_text().strip()
                return " ".join([s.strip() for s in text.splitlines() if s.strip()])
            else:
                print("the url for the course doesn't exist...")
        return []
    
    def save(self, fname=""):
        """save the current object into a file"""
        fname = self.title if len(fname) == 0 else fname
        with open(COURSE_PATH + fname, 'wb') as f:
            pickle.dump(self, f)

    def load(self, fname):
        """returns the saved course file"""
        try:
            with open(COURSE_PATH + fname, 'rb') as f:
                return pickle.load(f)
        except FileNotFoundError:
            print(f"this course: {fname}, doesn't exist... try making it...")
        return None
    
    def update(self):
        """update units in the course from handbook"""
        for code, unit in self.unitlist.units.items():
            if not type(unit):
                self.unitlist.units[code] = unit.update()

    
    def match_code(self, text):
        pattern = r'\b[a-zA-Z]{4}\d{4}\b|\b6 points\b|\b12 points\b|\b24 points\b|\b36 points\b|\b48 points\b'
        matches = re.findall(pattern, text)
        return matches  

    def is_code(self, ucode):
        """check if ucode is actually code"""
        return (len(ucode) == 8 and 
                ucode[4:].isnumeric() and
                ucode[:4].isalpha())
    

    def find_units(self) -> dict:
        """ Given the url of the course, fetch all the units outlined.
        """        
        text = self.text
        # cut out only the units in the course structure
        # some degrees have different layouts...
        if "Master of Professional Engineering" in text:
            prem = text[text.index("Course structure details"):
                        text.index("Biomedical Engineering specialisation")]
            after = text[text.index("Software Engineering specialisation"):
                        text.index("Meet our students")]
            after = after.replace("Take unit(s) to the value of 36 points", "Option - Take unit(s) to the value of 36 points")
            text = prem + " " + after
        elif "Software Engineering major units." in text:
            text = text[text.index("Software Engineering major units."):text.index("Course structure details Your degree options")]
        elif "Accreditation" in text:
            text = text[text.index("Course structure details"):text.index("Accreditation")]
        elif "Course accreditation" in text:
            text = text[text.index("Course structure details"):text.index("Course accreditation")]
        

        text = text.replace("Honours", "")
        text = text[text.index("Level 1"):]
        if "Level" in text:
            textlist = text.split("Level")[1:]
            if "Option" in text:
                textlist = [text.strip().split("Option") for text in textlist]
            else:
                textlist = [[text] for text in textlist]
        elif "Conversion" in text: #works for MIT
            textlist = [t.split("Option") for t in text.split("Core")]
        level = 0

        #keeps the list of conversion, core and option units
        core, option, conversion, bridging = {}, {}, {}, {}

        for text in textlist:
            options = []
            for i in range(len(text)):
                if any(["Conversion" in t for t in text]):
                    conversion[level] = self.match_code(text[0])
                    continue
                elif level == 0:
                    level += 1
                if "Bridging" in text[i]:
                    bridging[level] = self.match_code(" ".join(text[i].split("Bridging")[1:]))
                    text[i] = " ".join(text[i].split("Bridging")[:1])
                if i == 0:
                    core[level] = [code for code in self.match_code(text[i]) if self.is_code(code)]
                else:
                    options.append(self.match_code(text[i]))
            option[level] = options

            print(f"Level {level} Done!")
            level += 1

        # #up to 5 levels
        # for level in range(1, 6):
        #     core, option, conversion, text = self.get_units(core, option, conversion, level, text)

        return conversion, bridging, core, option
    


    def add_unitlist(self, unit, cat="core", level=-1, group=1):
        """add the unit to the unitlist"""
        level = int(unit.code[4]) if level == -1 else level
        if cat == "core":
            self.core[level].append(unit.code)
            self.unitlist.ulist.append(unit.code)
        # need to check adding options
        elif cat == "option":
            if len(self.option[level]) > 0:
                self.option[level][group].append(unit.code)
            else:
                self.option[level].append([unit.code])
            self.unitlist.ulist.append(unit.code)
        self.unitlist = UnitList(ulist=self.unitlist.ulist)

    def remove_unitlist(self, code, cat="core"):
        """remove the unit from the unitlist"""
        if cat == "core":
            for k, v in self.core.items():
                if code in v:
                    self.core[k].remove(code)
                    self.unitlist.ulist.remove(code)
        elif cat == "option":
            for k, v in self.option.items():
                for i in range(len(v)):
                    if code in v[i]:
                        self.option[k][i].remove(code)
                        self.unitlist.ulist.remove(code)
        self.unitlist = UnitList(ulist=self.unitlist.ulist)

    # write a method get_study_plan that returns a dictionary of the study plan for the course. The dictionary keys are the years and semesters (Y1S1, Y1S2, Y2S1, Y2S2, Y3S1, Y3S2, Y4S1, Y4S2) and the values are lists of the units that can be taken in that year. in each semester, at most 4 units can be taken. The values are unit codes that can be taken in that year. The prerequisites of each unit are checked to ensure that the unit is taken in later years if the prerequisite has not been met.
    def get_study_plan_s1(self) -> dict:
        
        # #duplicate self.core dictionary to avoid changing the original
        # all_units = copy.deepcopy(self.core)

        all_units = copy.deepcopy(self.study_plan_s1)
        #separating units based on semesters onto a new dictionary
        for k, v in self.core.items():
            for code in v:
                current_unit = self.unitlist[code]
                if 1 in current_unit.semester:
                    all_units[f"Y{k}S1"].append(code)
                if 2 in current_unit.semester:
                    all_units[f"Y{k}S2"].append(code)
        #now add option units to all_units
        for k, v in self.option.items():
            if len(v) > 0:
                for prereq_set in v:
                    if prereq_set[0] == "6 points":
                        i = 1
                        #skip units that are not offered
                        while len(self.unitlist[prereq_set[i]].semester) < 1 and i < len(prereq_set):
                            i += 1
                        available_sem = list(self.unitlist[prereq_set[i]].semester)[0]
                        all_units[f"Y{k}S{available_sem}"].append(prereq_set[i])
                    elif prereq_set[0] == "12 points": #there should be at least 2 units in the list
                        i = 1
                        #skip units that are not offered
                        while len(self.unitlist[prereq_set[i]].semester) < 1 and i < len(prereq_set):
                            i += 1
                        available_sem = list(self.unitlist[prereq_set[i]].semester)[0]
                        all_units[f"Y{k}S{available_sem}"].append(prereq_set[i])
                        i += 1
                        #skip units that are not offered for 2nd unit
                        while len(self.unitlist[prereq_set[i]].semester) < 1 and i < len(prereq_set):
                            i += 1
                        available_sem = list(self.unitlist[prereq_set[i]].semester)[0]
                        all_units[f"Y{k}S{available_sem}"].append(prereq_set[i])
        for k, v in all_units.items():
            print(k, sorted(v))               
        print("*"*50)
        
        #go through items in all_units and remove duplicates
        exists = set()
        remove = []
        for k, v in all_units.items():
            for code in v:
                if code in exists:
                    remove.append((k, code))
                else:
                    exists.add(code)
        for val in remove:
            all_units[val[0]].remove(val[1])
        

        #deal with honours project units that are 12 pts
        saved = ""
        first = False
        second = False
        for k, v in all_units.items():
            if len(saved) > 0:
                second = True
            for code in v:
                if code == "CITS4010" and not first:
                    all_units[k].append(code)
                    first = True
                elif (code == "CITS4011") and first:
                    saved = code
                    all_units[k].remove(code)
            if second:
                all_units[k].append(saved)
                all_units[k].append(saved)
                saved = ""
                second = False
            
    
          
        #now we will check the prerequisites of each unit
        covered = set()
        covered.add("MATH1721")
        covered.add("MATH1720")
        covered.add("MATH1012")
        for k, v in all_units.items():
            #making sure the units fit into sems
            year = int(k[1])
            sem = int(k[3])
            possible = []
            if len(v) > 4:
                for code in v:
                    #this checks if any units offered in both semesters
                    unit = self.unitlist[code]
                    if len(unit.semester) > 1 and unit.code not in HONOURS: #means availabled in both semesters
                        possible.append(code)
            if len(possible) > 0:
                move_code = possible[0] #just move the first option
                all_units[k].remove(move_code)
                if sem == 1:
                    all_units[f"Y{year}S2"].append(move_code)
                else:
                    all_units[f"Y{year+1}S1"].append(move_code)
            elif len(v) > 4:
                #let's check if we can move it up
                if year > 2 and sem == 1:
                    if len(all_units[f"Y{year-1}S1"]) < 4:
                        i = 0
                        while v[i] in HONOURS:
                            i += 1
                        move_code = v[i]
                        all_units[k].remove(move_code)
                        all_units[f"Y{year-1}S1"].append(move_code)
                    else:
                        #can't do anything about it with this unit.
                        pass
                elif year > 2 and sem == 2:
                    if len(all_units[f"Y{year-1}S2"]) < 4:
                        i = 0
                        print(v[i])
                        while v[i] in HONOURS:
                            i += 1
                        move_code = v[i]
                        all_units[k].remove(move_code)
                        all_units[f"Y{year-1}S2"].append(move_code)
                    else:
                        #can't do anything about it with this unit.
                        pass
                    


                #should scan further year units and avoid prereqs.
                pass


            #prereq checking part
            for code in v:
                unit = self.unitlist[code]
                if len(unit.prereqlist) > 0:
                    for prereqs in unit.prereqlist:
                        satisfied = True if set(prereqs).issubset(covered) else False
                        if satisfied:
                            #dont need to check other prerequisites
                            break
                    if not satisfied:
                        #do something about sorting out prereq
                        print(prereqs)
                        print(f"{code} NOT COVERED")
                        pass

                #all passed, so add it to the covered set
                covered.add(code[:8])
                


        
        for k, v in all_units.items():
            print(k, sorted(v))
        #combines the core and option units into one dictionary
        # for k, v in self.option.items():
        #     if len(v) > 0:
        #         for options in v:
        #             all_units[k].append(options[0])

        #using all_units we will populate the self.study_plan dictionary
        #the keys are the years and semesters (Y1S1, Y1S2, Y2S1, Y2S2, Y3S1, Y3S2, Y4S1, Y4S2)



        # print(self.core)
        # print("*" * 20)
        # print(self.option)
        # print("*" * 20)
        # print(all_units)








def url_check(code):
    """check the code data from web"""
    response = requests.get(UnitList.URL + code)
    soup = BeautifulSoup(response.text, "html.parser")
    return [s.strip() for s in soup.get_text().splitlines() if s.strip()]


if __name__ == "__main__":
    ##################
    ###    UNIT    ###
    ##################
    # # you can make your own unit by providing the unit code as follows.
    # # by default it will retrieve the info from the handbook.
    # unit = Unit("CITS1001")

    # # if you have the unit in file, you can load it like this
    # # if it fails, it will try to load from the handbook.
    # unit = Unit()
    # unit = unit.load("CITS1003")

    # # you might want to update the unit with new contents from the handbook   
    # unit = Unit()
    # unit = unit.load("CITS1003")
    # unit.description = "hello."
    # print(unit)
    # unit = unit.update()
    # print(unit)

    # # you can save unit too which uses default name as the code of the unit.
    # # you can edit content and save it using another name.
    # unit = Unit()
    # unit = unit.load("CITS1003")
    # unit.description = "hello."
    # unit.code = "CITS1003b"
    # unit.prereq = "CITS1001 or CITS1401"
    # unit.semester = [2]
    # unit.save("CITS1003b")
    # unit = unit.load("CITS1003b")
    # print(unit)
    # print(unit.prereqlist)
    # print(Unit().load("CITS1003"))
    # print(Unit().load("CITS1003").prereqlist)


    ######################
    ###    UNIT LIST   ###
    ######################
    # # without any parameters, it creats an empty unitlist.
    # # if fname exists, it loads the units from the fname
    # # if you can pass in the list of unit codes as string, it will load those units.
    # # if fname exists, it ignores the input list.
    # unitlist = UnitList()
    # unitlist = UnitList(fname="unit_list.txt")
    # unitlist = UnitList(ulisit=["CITS1003", "CITS1401"])

    # # set your new fname, any changes will be saved here.
    # unitlist.set_fname("new_list.txt")

    # # below code scans all units (e.g., CITS1000 to CITS6000) and saves them
    # # edit the code and stop to discover a subset
    # # this method is used usually first time to populate the units
    # unitlist.find_units('CITS1000', stop="6000")

    # # You can clean up your unit files by calling this
    # # it will go over your current list from unit_list.txt and delete
    # # ones no longer available in the handbook.
    # unitlist.remove_none_units()

    # # You can output the current units as text in the unitlist as follows.
    # # by default it will save to its own file name, but you can specify other names.
    # unitlist.save()
    # unitlist.save("hello.txt")


    ####################
    ###    COURSE    ###
    ####################
    # # you can create an empty course and populate it later
    # course = Course()

    # # you can create the course from giving a URL
    # course = Course(url="https://www.uwa.edu.au/study/Courses/International-Cybersecurity")
    # course = Course(url="https://www.uwa.edu.au/study/Courses/Artificial-Intelligence")
    # course = Course(url="https://www.uwa.edu.au/study/Courses/Computing-and-Data-Science")
    # course = Course(url="https://www.uwa.edu.au/study/Courses/Software-Engineering")
    # course = Course(url="https://www.uwa.edu.au/study/courses/master-of-information-technology")
    # course = Course(url="https://www.uwa.edu.au/study/courses/data-science")
    # MPE import needs work...
    # course = Course(url="https://www.uwa.edu.au/study/courses/master-of-professional-engineering")
    

    # # you can also load courses from saved course files
    # course = Course().load("Artificial Intelligence")
    # course = Course().load("Artificial Intelligence 2024")
    # course = Course().load("International Cybersecurity")
    # course = Course().load("International Cybersecurity 2024")
    course = Course().load("Computing and Data Science")
    # course = Course().load("Data Science 2024")
    # print(course)
    # # update the course units' contentsx from handbook by updating
    # course.update()

    # # you can save courses using the save method.
    # # the title is used as the file name, unless provided
    # course.save()
    # course.save("some_name")

    # print(course)
    print(course.get_study_plan_s1())

 

    pass




