# Fictional name pools for the demo dataset.
#
# The names are generic South Indian / Indian given names and surnames chosen to
# make the demo look realistic. They do not refer to any real individual.

MALE_FIRST_NAMES = [
    "Arjun", "Rahul", "Vivek", "Nikhil", "Anand", "Sreejith", "Harish",
    "Manoj", "Deepak", "Rakesh", "Sanjay", "Vishnu", "Ajith", "Prasad",
    "Ranjith", "Kiran", "Sooraj", "Ratheesh", "Midhun", "Jithin", "Aravind",
    "Gokul", "Naveen", "Sandeep", "Vipin", "Akhil", "Rohit", "Sujith",
    "Anoop", "Bibin", "Dinesh", "Faisal", "Gautham", "Hari", "Irfan",
    "Jaison", "Krishna", "Lijo", "Mithun", "Nithin",
]

FEMALE_FIRST_NAMES = [
    "Meera", "Anjali", "Diya", "Sneha", "Lakshmi", "Divya", "Anjana",
    "Reshma", "Aiswarya", "Nithya", "Sreelakshmi", "Parvathy", "Anjitha",
    "Sona", "Vidya", "Rekha", "Shilpa", "Neethu", "Arya", "Gayathri",
    "Bhavana", "Chithra", "Deepthi", "Elena", "Fathima", "Geethu", "Haritha",
    "Indu", "Jasmine", "Kavya", "Laya", "Manju", "Nandini", "Omana",
    "Priya", "Riya", "Sandra", "Teena", "Uma", "Veena",
]

SURNAMES = [
    "Menon", "Nair", "Varma", "Krishnan", "Thomas", "Mathew", "Joseph",
    "Pillai", "Kurup", "Warrier", "Rajan", "Nambiar", "Varghese", "Iyer",
    "Das", "George", "Kumar", "Rao", "Sharma", "Vijayan", "Suresh",
    "Anilkumar", "Balakrishnan", "Chandran", "Gopinath", "Harikumar",
    "Jayaraj", "Krishnakumar", "Lal", "Mohan", "Narayanan", "Padmanabhan",
    "Raghunath", "Sasidharan", "Unnikrishnan", "Venugopal",
]

CITIES = [
    "Kochi", "Ernakulam", "Thrippunithura", "Aluva", "Kakkanad", "Perumbavoor",
    "Angamaly", "Kalamassery", "Muvattupuzha", "Fort Kochi", "Palarivattom",
    "Vyttila", "Edappally", "Thevara", "Maradu",
]

STREETS = [
    "MG Road", "Marine Drive", "Chittoor Road", "Banerji Road", "SA Road",
    "Kaloor Junction", "Panampilly Nagar", "Kadavanthra", "Vyttila Mobility Hub Road",
    "Infopark Road", "Seaport-Airport Road", "Bypass Junction",
]

RELATIONS = ["Spouse", "Son", "Daughter", "Father", "Mother", "Brother", "Sister", "Guardian"]

ALLERGY_POOL = [
    "Penicillin", "Sulfa drugs", "Aspirin", "Latex", "Dust", "Peanuts",
    "Shellfish", "Iodine contrast", "Pollen", "Lactose", "No known allergies",
]

HISTORY_POOL = [
    "Type 2 diabetes mellitus, on oral hypoglycaemics.",
    "Essential hypertension, well controlled on medication.",
    "Bronchial asthma since childhood, uses inhaler as needed.",
    "Hypothyroidism on replacement therapy.",
    "Previous appendicectomy (2018).",
    "Chronic kidney disease stage 2 under nephrology follow-up.",
    "Dyslipidaemia with elevated LDL, on statin therapy.",
    "Migraine without aura, episodic.",
    "Osteoarthritis of both knees, conservative management.",
    "No significant past medical history reported.",
    "Anemia in pregnancy, under treatment.",
    "Coronary artery disease, post angioplasty (2021).",
]

CHRONIC_POOL = [
    "Diabetes", "Hypertension", "Asthma", "Hypothyroidism", "CKD",
    "Dyslipidaemia", "CAD", "Arthritis", "None",
]

BLOOD_GROUPS = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]
BLOOD_WEIGHTS = [22, 4, 26, 5, 8, 2, 29, 4]

COMPLAINTS = {
    "Cardiology": [
        "Chest discomfort on exertion",
        "Palpitations with breathlessness",
        "Follow-up for hypertension",
        "Swelling of both legs",
    ],
    "Neurology": [
        "Recurrent headache with giddiness",
        "Numbness of right hand",
        "Follow-up for seizure disorder",
        "Tremor of both hands",
    ],
    "Orthopedics": [
        "Knee pain while climbing stairs",
        "Lower back pain after lifting",
        "Follow-up after fracture immobilisation",
        "Shoulder stiffness",
    ],
    "General Medicine": [
        "Fever with body ache for three days",
        "Generalised weakness and fatigue",
        "Follow-up for diabetes review",
        "Cough with sore throat",
    ],
    "Pediatrics": [
        "Fever and reduced appetite",
        "Routine immunisation visit",
        "Recurrent cough at night",
        "Loose stools since yesterday",
    ],
    "Gynecology": [
        "Menstrual irregularity",
        "Lower abdominal discomfort",
        "Antenatal check-up",
        "Follow-up for PCOS",
    ],
    "Dermatology": [
        "Itchy rash over both arms",
        "Acne over face",
        "Hair fall evaluation",
        "Patchy discolouration of skin",
    ],
    "ENT": [
        "Ear pain with reduced hearing",
        "Nasal blockage and sneezing",
        "Sore throat with hoarseness",
        "Ringing sensation in the ear",
    ],
    "Ophthalmology": [
        "Blurred vision for distance",
        "Redness and watering of the eye",
        "Routine refraction check",
        "Follow-up for cataract evaluation",
    ],
}

DEFAULT_COMPLAINTS = [
    "Routine review consultation",
    "Follow-up visit",
    "New complaint requiring evaluation",
    "General health check-up",
]

EMERGENCY_COMPLAINTS = [
    "Road traffic accident, blunt trauma to chest",
    "Acute breathlessness with low oxygen saturation",
    "Severe chest pain radiating to the left arm",
    "Sudden onset weakness of left side of body",
    "High grade fever with altered sensorium",
    "Acute abdominal pain with vomiting",
    "Fall from height with suspected limb injury",
    "Poisoning - organophosphate exposure (demo case)",
    "Severe allergic reaction after food",
    "Profuse bleeding from laceration",
]

SURGERY_NAMES = {
    "Cardiology": ["Coronary angiogram with stenting", "Permanent pacemaker implantation"],
    "General Surgery": ["Laparoscopic cholecystectomy", "Open appendicectomy", "Hernia mesh repair"],
    "Orthopedics": ["Knee arthroscopy", "Dynamic hip screw fixation", "Total knee replacement"],
    "Neurology": ["Lumbar laminectomy", "Craniotomy for evacuation of hematoma"],
    "Obstetrics": ["Emergency caesarean section", "Normal vaginal delivery support"],
    "Gynecology": ["Laparoscopic hysterectomy", "Ovarian cystectomy"],
    "Oncology": ["Modified radical mastectomy", "Excision of soft tissue tumour"],
    "ENT": ["Septoplasty", "Tonsillectomy"],
    "Ophthalmology": ["Phacoemulsification with IOL", "Pterygium excision"],
    "Urology": ["Ureteroscopic stone removal"],
    "Nephrology": ["Arteriovenous fistula creation"],
}

DEFAULT_SURGERY = ["Diagnostic laparoscopy", "Abscess drainage"]

DEPARTMENT_DESCRIPTIONS = {
    "Cardiology": "Comprehensive heart care including interventional cardiology, echocardiography and cardiac rehabilitation.",
    "Neurology": "Diagnosis and management of disorders of the brain, spinal cord, nerves and muscles.",
    "Orthopedics": "Joint replacement, arthroscopy, trauma and sports injury services.",
    "General Medicine": "Adult internal medicine, chronic disease management and preventive health.",
    "General Surgery": "Elective and emergency general surgical procedures with a day-care unit.",
    "Pediatrics": "Newborn, child and adolescent health with a dedicated paediatric ICU.",
    "Gynecology": "Women's health, minimally invasive gynaecological surgery and fertility services.",
    "Obstetrics": "Antenatal, delivery and postnatal care with a level-3 maternity unit.",
    "Dermatology": "Skin, hair and nail disorders with phototherapy and cosmetic dermatology.",
    "ENT": "Ear, nose and throat surgery including endoscopic sinus and micro-ear surgery.",
    "Ophthalmology": "Cataract, glaucoma, retina and refractive services.",
    "Oncology": "Medical, surgical and radiation oncology with a day-care chemotherapy unit.",
    "Nephrology": "Kidney care, dialysis unit and transplant follow-up.",
    "Gastroenterology": "Diagnostic and therapeutic endoscopy with hepatology services.",
    "Pulmonology": "Respiratory medicine, bronchoscopy and pulmonary function testing.",
    "Psychiatry": "Mental health assessment, counselling and de-addiction services.",
    "Emergency Medicine": "24x7 emergency and trauma care with a dedicated resuscitation bay.",
    "Radiology": "CT, MRI, ultrasound, X-ray and interventional radiology services.",
    "Pathology": "Laboratory medicine including haematology, biochemistry and microbiology.",
    "Anesthesiology": "Perioperative anaesthesia services and a pain clinic.",
}
