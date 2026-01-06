GST_STATES = [
    "01 - Jammu & Kashmir",
    "02 - Himachal Pradesh",
    "03 - Punjab",
    "04 - Chandigarh",
    "05 - Uttarakhand",
    "06 - Haryana",
    "07 - Delhi",
    "08 - Rajasthan",
    "09 - Uttar Pradesh",
    "10 - Bihar",
    "11 - Sikkim",
    "12 - Arunachal Pradesh",
    "13 - Nagaland",
    "14 - Manipur",
    "15 - Mizoram",
    "16 - Tripura",
    "17 - Meghalaya",
    "18 - Assam",
    "19 - West Bengal",
    "20 - Jharkhand",
    "21 - Odisha",
    "22 - Chattisgarh",
    "23 - Madhya Pradesh",
    "24 - Gujarat",
    "25 - Daman & Diu",
    "26 - Dadra & Nagar Haveli",
    "27 - Maharashtra",
    "28 - Andhra Pradesh (Old)",
    "29 - Karnataka",
    "30 - Goa",
    "31 - Lakshadweep",
    "32 - Kerala",
    "33 - Tamil Nadu",
    "34 - Puducherry",
    "35 - Andaman & Nicobar Islands",
    "36 - Telangana",
    "37 - Andhra Pradesh (New)",
    "38 - Ladakh"
]

def get_state_list():
    # Convert to format "StateName (Code)" or keep as "Code - Name"?
    # User screenshot showed "Maharashtra (27)". 
    # Let's reformat to match user preference: "Name (Code)"
    formatted = []
    for s in GST_STATES:
        parts = s.split(" - ")
        code = parts[0]
        name = parts[1]
        formatted.append(f"{name} ({code})")
    return sorted(formatted)
