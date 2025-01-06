from bs4 import BeautifulSoup
import requests
from unidecode import unidecode
from time import sleep
from user_agents import data
import random

# Use a "User Agent" so the computer would register as a human
# Data includes 3000+ variations of user agents so we can select a random user agent everytime the program runs, stimulating different devices and browsers 
# The list includes users from: 
    # https://github.com/fake-useragent/fake-useragent/blob/master/src/fake_useragent/data/browsers.json
    # https://github.com/THAVASIGTI/pyuser_agent/blob/master/pyuser_agent/store_dump.json
def set_headers(user_agent):
    return {
        'content-type': 'text/html;charset=UTF-8',
        'Accept-Encoding': 'gzip, deflate, sdch',
        'Accept-Language': 'en-US,en;q=0.8',
        'User-Agent': user_agent,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    }
random_user_agent = random.choice(data)
HEADERS = set_headers(random_user_agent)

# Removes characters in non recognizable fonts and commas (because that signifies new cell in CSV)
def remove_non_ascii(text):
    num_str = ""
    if text:
        for i in text:
            if i != ",":
                num_str = num_str + i
    return unidecode(text)

# Used when the values are described with their units. Ex. switching 16 GB to the number 16
def get_num_from_str(s):
    num_str = ""
    for i in s:
        if ((i.isdigit() or i == '.') and i != ",") :
            num_str = num_str + i
    return unidecode(num_str)

def specific_data_from_table(table_data, val1, val2):
    if ("Chipset Brand" not in val1) and ("Processor Brand" not in val1) and ("Brand" in val1):
        table_data["Brand"] = val2
    # To get flow rate in a consistent manner (can be written as "Max flow rate", "Maximum flow rate" or just "Flow rate" -- we want to get either way)
    elif "Flow Rate" in val1:
        table_data["Flow Rate"] = val2
    elif "Color Rendering Index" in val1 or "CRI" in val1:
        table_data["Color Rendering Index (CRI)"] = val2
    elif "Base" in val1:
        table_data["Base Material"] = val2
    else:
        table_data[val1] = val2
    
# There are multiple tables with similar formats, so this is a general function to extract information from a table into key-value pairs
def get_data_from_table(table, table_data):
    if table is not None:
        col1 = [header.text.strip() for header in table.find_all('th')]
        col2 = table.find_all('tr') 
        # First table format keeps col1 under th tags and the second under tr tags
        if (len(col1) > 0):
            row = 0 
            # For each row in the second column, find the value and pair it with the coraspponding value in col1
            for c in col2:
                values = c.find('td')  # value of the second col
                if values:
                    val = values.text.replace('\u200e', '').replace(",", " ").strip() # removing the \u200e that appears in the beg of every value
                    # in case they write Brand Name instead of Brand or something along these lines
                    if (row < len(col1)):
                        specific_data_from_table(table_data, col1[row], val)
                        row += 1
        # Second table format doesn't have th
        else:
            for c in col2:
                left_values = c.find("span", attrs={"class": "a-size-base a-text-bold"})  # value of the second col
                if left_values:
                    left_val = left_values.text.replace('\u200e', '').replace(",", " ").strip() # removing the \u200e that appears in the beg of every value
                right_values = c.find("span", attrs={"class": "a-size-base po-break-word"})
                if right_values:
                    right_val = right_values.text.replace('\u200e', '').replace(",", " ").strip() # removing the \u200e that appears in the beg of every value
                specific_data_from_table(table_data, left_val, right_val)
    
# Using the values from handle_csv, returns the price
def price(item_convert_to_html):
    try:
        item_price = item_convert_to_html.find("div", attrs={"id": "corePrice_feature_div"})\
            .find("span", attrs={"class": "a-offscreen"})        
        item_price = item_price.text.strip()
        item_price = "$" + str(get_num_from_str(item_price))
    except AttributeError:
        item_price = "N/A"
    return item_price

# returns the title of the product
def get_title(item_convert_to_html):
    try:
        item_title = item_convert_to_html.find("span", attrs={"id": "productTitle"})
        item_title = item_title.text.strip()
    except AttributeError:
        item_title = "N/A"
    return remove_non_ascii(item_title)

# NOTE: NOT IN USE since we cannot set the Amazon location to CA.
# Using the values from handle_csv, returns if the item is for sale in CA
def for_sale_in_ca(item_convert_to_html):
    item_ca = "N/A"
    try:
        # a-color-error represents errors in regards to shipping. It includes messages like "Only 3 items left in stock - order soon" and "This item is not available"
        item_ca = item_convert_to_html.find("span", attrs={"class":"a-color-error"})
        # Error messages have many variations, but most of them start with "This item cannot be delivered..."
        # Checking if the error starts with the word "This" to make sure it's a delivery error
        if item_ca.text.strip()[0:4] == "This":
            item_ca = "No"
        else:
            item_ca = "Yes"
    except AttributeError:
        item_ca = "Yes"
    return item_ca

# Using the values from handle_csv, returns the ASIN
def asin(using_detail_bullet_list, item_convert_to_html, table_data):
    item_asin = "N/A"
    if using_detail_bullet_list == False:
        try:
            item_asin = item_convert_to_html.find("table", attrs={"id":"productDetails_detailBullets_sections1"})\
                .find("td", attrs={"class": "a-size-base prodDetAttrValue"})\
                .text.strip()
        except AttributeError:
            item_asin = "N/A"
    else:
        special_appliances(table_data, "ASIN", False)
    if item_asin == "N/A":
        item_asin = item_convert_to_html.find('input', {'id':'attach-baseAsin'})
        if (item_asin):
            item_asin = item_asin.get('value')    
    if item_asin == None:
        item_asin = item_convert_to_html.find('input', {'id':'ASIN'})
        if (item_asin):
            item_asin = item_asin.get('value')
    if item_asin == None: 
        item_asin = "N/A"
    return remove_non_ascii(item_asin)

def ship_from_sold_by(item_convert_to_html):
    result = ["N/A", "N/A"] # [ship from, sold by]
    # Found in a grid where the right side of the grid (the data we want) is under the following tag. Need only the first two rows of the grid; the rest is not interesting to us.
    right_grid = item_convert_to_html.findAll("span", attrs={"class": "a-size-small offer-display-feature-text-message"}) # Actual value 
    left_grid = item_convert_to_html.findAll("span", attrs={"class": "a-size-small a-color-tertiary"}) # Title (ship from, sold by)
    # Remove non text values from the grid
    left_grid_text = []
    for item in left_grid:
        item = item.text.strip()
        if (item not in left_grid_text):
            left_grid_text.append(item)
            
    right_grid_text = [item.text.strip() for item in right_grid]       

    for index, item in enumerate(left_grid_text):
        if item == "Ships from":
            result[0] = remove_non_ascii(right_grid_text[index])
        if item == "Sold by":
            result[1] = remove_non_ascii(right_grid_text[index])
    return result

# General code to get extra info about specific materials (ex. flow rate for plumbing fittings)
# table_data: a dict that holds value similarly the following example - "Flow Rate": 1.7
    # Ex. table_data["Flow Rate"] would return 1.7
# Type is the name of the value you want to find in table_date (value in the brackets)
# isNum checks if you want to covert the string that would be returned to an in
    # Ex. if table_data["Flow Rate"] returns 1.7 Gallons Per Minute, if isNum == True, it will convert it to 1.7
def special_appliances(table_data, type, isNum):
    if type in table_data:
        if (isNum):
            return get_num_from_str(table_data[type])
        return remove_non_ascii(table_data[type])
    return "N/A"

def isFileEmpty(has_headers):
    if (has_headers == 1):
        return False
    return True

# After getting a URL, we can get values from the page
all_data = {}
def handle_csv(URL, item_appliance, count_products, isFirstAttempt, has_headers):
    print("in handle csv")
    # Sessions help to maintain a consistent user expereinces. It saves cookies across requests, making it more efficent to connect to Amazon
    session = requests.Session()
    # Use a "User Agent" so the computer would register as a human
    # Added a Python library that creates a random user agent everytime the program runs, stimulating different devices each time
    random_user_agent = random.choice(data)
    HEADERS = set_headers(random_user_agent)
    session.headers.update(HEADERS)

    if (isFirstAttempt):
        count_products += 1
        all_data["item_model_number"] = "N/A"
        all_data["item_mfr"] = "N/A"
        all_data["brand"] = "N/A"
        all_data["ship_from"] = "N/A"
        all_data["sold_by"] = "N/A"
        all_data["price"] = "N/A"
        all_data["asin"] = "N/A"
        all_data["price_per_unit"] = "N/A"
        all_data["prod_title"] = "N/A"
        # Wants to switch the connection every 5 products:
        if (count_products % 5 == 0):
            session.close()
            session = requests.Session()
            random_user_agent = random.choice(data)
            # Headers for request
            HEADERS = set_headers(random_user_agent)
            session.headers.update(HEADERS)

    # Getting data from the item's page 
    item_webpage = session.get(URL, allow_redirects=True)
    item_convert_to_html = BeautifulSoup(item_webpage.content, "html.parser")

    # --- PRICE --- 
    if (all_data["price"] == "N/A"):
        item_price = price(item_convert_to_html)
        all_data["price"] = item_price
    # --- TITLE ---
    if (all_data["prod_title"] == "N/A"):
        all_data["prod_title"] = get_title(item_convert_to_html)
        print(all_data["prod_title"])
    
    # --- PRODUCT INFORMATION DETAILS ---
    # Convert specification table into a dict     
    table_data = {}
    item_model_number = "N/A" 
    # Finds the correct table on Amazon. There are two tables under that section, and people can decide which one to use when listing an item
    # Checking which table is being used and parsing that
    using_detail_bullet_list = False
    table = item_convert_to_html.find("table", attrs={"id": "productDetails_techSpec_section_1"})
    if table is None:
        using_detail_bullet_list = True
        table = item_convert_to_html.find("table", attrs={"id": "productDetails_detailBullets_sections1"})
    if table is not None:
        get_data_from_table(table, table_data)
    # Probably using a list instead of a table
    list = item_convert_to_html.find("ul", attrs={"class": "a-unordered-list a-nostyle a-vertical a-spacing-none detail-bullet-list"})
    if (list):
        rows = list.find_all("span", attrs={"class": "a-list-item"})
        for row in rows:
            val1 = row.find("span", attrs={"class": "a-text-bold"})
            val2 = val1.findNext("span")
            specific_data_from_table(table_data, val1.text.replace(":", "").replace('\u200f', '').replace('\u200e', '').replace(",", " ").strip(), val2.text.replace('\u200f', '').replace('\u200f', '').replace(",", " ").strip())
    # Having an "important information section" rather than a normal list/table
    list = item_convert_to_html.find("div", attrs={"class": "a-section a-spacing-extra-large bucket"})
    if (list):
        rows = list.find_all("div", attrs={"class": "a-section content"})
        for row in rows:
            val1 = row.find("span", attrs={"class": "a-text-bold"})
            if (val1):
                val2 = val1.findNext("p").findNext("p")
                specific_data_from_table(table_data, val1.text.strip(), val2.text.strip())

    # might have two tech spec sections
    table = item_convert_to_html.find("table", attrs={"class": "a-normal a-spacing-micro"})
    get_data_from_table(table, table_data)
    # Features and specs section
    table2 = item_convert_to_html.find("table", attrs={"id": "productDetails_techSpec_section_2"})
    get_data_from_table(table2, table_data)
    # table at the top of the page
    table1 = item_convert_to_html.find("table", attrs={"id": "productDetails_techSpec_section_1"})
    get_data_from_table(table1, table_data)
    # New Amazon layout page
    table3 = item_convert_to_html.find_all("table", attrs={"class": "a-keyvalue prodDetTable", "role":"presentation"})
    for t in table3:
        get_data_from_table(t, table_data)
    if (all_data["item_mfr"] == "N/A"):
        item_mfr = special_appliances(table_data, "Manufacturer", False)
        all_data["item_mfr"] = item_mfr
    if (all_data["brand"] == "N/A"):
        item_brand = special_appliances(table_data, "Brand", False)
        all_data["brand"] = item_brand
    print("FINISHED TABLES")
    # Calculates price per item
    item_number = special_appliances(table_data, "Unit Count", True)
    if item_number != "N/A" and all_data["price_per_unit"] == "N/A":
        all_data["price_per_unit"] = float(get_num_from_str(all_data["price"])) / float(item_number)
        all_data["price_per_unit"] = "$" + str(round(all_data["price_per_unit"], 2))
    if all_data["price_per_unit"] != "N/A":
        all_data["price"] = all_data["price_per_unit"]
    # Get item model number, if it doesn't exist, use the part number or model name
    if (all_data["item_model_number"] == "N/A"): 
        if "Item model number" in table_data:
            item_model_number = remove_non_ascii(table_data["Item model number"])
        elif "Model Number" in table_data:
            item_model_number = remove_non_ascii(table_data["Model Number"])
        elif "Part Number" in table_data:
            item_model_number = remove_non_ascii(table_data["Part Number"])
        elif "Model Name" in table_data:
            item_model_number = remove_non_ascii(table_data["Model Name"])
        all_data["item_model_number"] = item_model_number
    # --- ASIN ---
    # If ASIN is found on the table we parsed, use the dict we made.
    # If it's on the other table, get the first row of the table
    item_asin = asin(using_detail_bullet_list, item_convert_to_html, table_data)
    if (all_data["asin"] == "N/A"):
        if item_asin == "N/A" and "ASIN" in table_data:
            item_asin = remove_non_ascii(table_data["ASIN"])
        all_data["asin"] = item_asin

    # --- Ship from and Sold by ---
    result = ship_from_sold_by(item_convert_to_html)
    if (all_data["ship_from"] == "N/A"):
        ship_from = result[0]
        all_data["ship_from"] = ship_from
    if (all_data["sold_by"] == "N/A"):
        sold_by = result[1]
        all_data["sold_by"] = sold_by
    
    # Special Features for Specific Appliance Types
    sent_text = ""
    # --- ROOM AC ---
    if item_appliance.lower() == "room ac":
        if isFileEmpty(has_headers):
            title = "Model #,Manufacturing Company,Brand,Ship from,Sold by,Appliance Type,Rated Input,Rated Current,Cooling Capacity,Power Supply,Certified to MAEDbS?,ASIN,Retail Price,Retail Link,Notes\n"
            sent_text += title
        item_volt = special_appliances(table_data, "Voltage", True)
        item_watt = special_appliances(table_data, "Wattage", True)
        item_cooling = special_appliances(table_data, "Cooling Power", False)
        item_current = special_appliances(table_data, "Current Rating", False)
        if isFirstAttempt == False:
            sent_text += f"{all_data['item_model_number']}, {all_data['item_mfr']}, {all_data['brand']}, {all_data['ship_from']}, {all_data['sold_by']}, {item_appliance.title()}, {item_volt}, {item_current}, {item_cooling}, {item_watt}, , {all_data['asin']}, {all_data['price']}, {URL}, "
    # --- CENTRAL AC ---
    elif item_appliance.lower() == "central ac":
        if isFileEmpty(has_headers):
            title = "Model #,Manufacturing Company,Brand,Ship from,Sold by,Appliance Type,Voltage,Energy Efficiency Ration (EER),Electric Input @95° (Watts),Cooling Capacity @95° (BTUH),Certified to MAEDbS?,ASIN,Retail Price,Retail Link,Notes\n"
            sent_text += title
        item_volt = special_appliances(table_data, "Voltage", True)
        item_watt = special_appliances(table_data, "Wattage", True)
        item_capacity = special_appliances(table_data, "Cooling Power", True)
        item_seer = special_appliances(table_data, "Seasonal Energy Efficiency Ratio (SEER)", True)
        if isFirstAttempt == False:
            sent_text += f"{all_data['item_model_number']}, {all_data['item_mfr']}, {all_data['brand']}, {all_data['ship_from']}, {all_data['sold_by']}, {item_appliance.title()}, {item_volt}, {item_seer}, {item_watt}, {item_capacity}, , {all_data['asin']}, {all_data['price']}, {URL}, "
    # --- WATER HEATERS ---
    elif item_appliance.lower() == "water heaters":
        if isFileEmpty(has_headers):
            title = "Model #,Manufacturing Company,Brand,Ship from,Sold by,Appliance Type,Rated Volume,Max gal/min,Input Rating,Annual Fossil Fuel Energy Consumption,Certified to MAEDbS,ASIN,Retail Price,Retail Link,Notes\n"
            sent_text += title
        item_volume = special_appliances(table_data, "Size", False) # rated volume, in gallons
        item_consumption = special_appliances(table_data, "Flow Rate", True) # Max gal/min
        if (item_consumption == "N/A"):
            item_consumption = special_appliances(table_data, "Water Consumption", True)
        item_input = special_appliances(table_data, "Wattage", False) # input rating, I get it from Watts
        item_fossil = special_appliances(table_data, "Heat Output", False) # Annual fossil fuel energy consumption, I get it based on British Thermal Units
        item_note = ""
        if (item_fossil != "N/A" or item_volume != "N/A"):
            item_note = "Rated volume is based on the value under \"Size\" and Fossil energy consumption is based on the value under \"Heat Output\". Most companies put the right info but please make sure that the value is in the correct units."
        if isFirstAttempt == False:
            sent_text += f"{all_data['item_model_number']}, {all_data['item_mfr']}, {all_data['brand']}, {all_data['ship_from']}, {all_data['sold_by']}, {item_appliance.title()}, {item_volume}, {item_consumption}, {item_input}, {item_fossil}, {item_note}, {all_data['asin']}, {all_data['price']}, {URL}, "
    # --- PLUMBING FITTINGS ---
    elif item_appliance.lower() == "plumbing fittings":
        if isFileEmpty(has_headers):
            title = "Model #,Manufacturing Company,Brand,Ship from,Sold by,Series Name,Appliance Type,Advertised Flow Rate,Certified to MAEDbS?,ASIN,Retail Price,Retail Link,Notes\n"
            sent_text += title
        item_series = "N/A" # Series name (if applicable)
        item_flow_rate = special_appliances(table_data, "Flow Rate", True) # Advertised Flow Rate
        if isFirstAttempt == False:
            sent_text += f"{all_data['item_model_number']}, {all_data['item_mfr']}, {all_data['brand']}, {all_data['ship_from']}, {all_data['sold_by']}, {item_series}, {item_appliance.title()}, {item_flow_rate}, ,{all_data['asin']}, {all_data['price']}, {URL}, "
    # --- PLUMBING FIXTURES ---
    elif item_appliance.lower() == "plumbing fixtures":
        if isFileEmpty(has_headers):
            title = "Model #,Manufacturing Company,Brand,Ship from,Sold by,Appliance Type,Flow Rate (GPF),Certified to MAEDbS?,ASIN,Retail Price,Retail Link,Notes\n"
            sent_text += title
        item_flow_rate = special_appliances(table_data, "Water Consumption", True) # Flow Rate (GPF)
        if isFirstAttempt == False:
            sent_text += f"{all_data['item_model_number']}, {all_data['item_mfr']}, {all_data['brand']}, {all_data['ship_from']}, {all_data['sold_by']}, {item_appliance.title()}, {item_flow_rate}, , {all_data['asin']}, {all_data['price']}, {URL}, "
    # --- LAMPS ---
    elif item_appliance.lower() == "lamps":        
        if isFileEmpty(has_headers):
            title = "Model #,Manufacturing Company,Brand,Ship from,Sold by,Appliance Type,Base Type,Bulb Shape,Lumens,Watts,Color Term,Life,CRI,Lumens/watt,Efficacy,Certified to MAEDbS?,ASIN,Retail Price,Retail Link,Notes\n"
            sent_text += title
        lamp_base = special_appliances(table_data, "Base Material", False)
        lamp_bulb = special_appliances(table_data, "Bulb Shape Size", False)
        lamp_lum = special_appliances(table_data, "Luminous Flux", True)
        if (lamp_lum == "N/A"):
            lamp_lum = special_appliances(table_data, "Brightness", True)
        lamp_watt1 = special_appliances(table_data, "Wattage", True)
        lamp_watt = special_appliances(table_data, "Light Source Wattage", True)
        # Lamps often display both the watt and watt equivalance, this makes sure we get the smaller number
        if (lamp_watt == "N/A"):
            lamp_watt = lamp_watt1
        elif (lamp_watt1 != "N/A" and lamp_watt != "N/A"):
            lamp_watt = float(lamp_watt)
            lamp_watt1 = float(lamp_watt1)
            if (lamp_watt1 < lamp_watt):
                lamp_watt = lamp_watt1
        lamp_temp = special_appliances(table_data, "Color Temperature", True)
        lamp_life = special_appliances(table_data, "Average Life", True)
        lamp_cri = special_appliances(table_data, "Color Rendering Index (CRI)", True)
        lamp_lum_wat = "N/A"
        lamp_compliance = "N/A"
        if lamp_lum != "N/A" and lamp_watt != "N/A":
            lamp_lum_wat = round(float(lamp_lum) / float(lamp_watt), 2)
        if lamp_lum_wat != "N/A" and lamp_cri != "N/A":
            lamp_compliance = round(2.3 * float(lamp_lum_wat) + float(lamp_cri), 2)
        if isFirstAttempt == False:
           sent_text += f"{all_data['item_model_number']}, {all_data['item_mfr']}, {all_data['brand']}, {all_data['ship_from']}, {all_data['sold_by']}, {item_appliance.title()}, {lamp_base}, {lamp_bulb}, {lamp_lum}, {lamp_watt}, {lamp_temp}, {lamp_life}, {lamp_cri}, {lamp_lum_wat}, {lamp_compliance}, , {all_data['asin']}, {all_data['price']}, {URL}, "
    else: 
        if isFileEmpty(has_headers):
            title = "Model #,Manufacturing Company,Brand,Ship from,Sold by,Appliance Type,Certified to MAEDbS?,ASIN,Retail Price,Retail Link,Notes\n"
            sent_text += title   
        if isFirstAttempt == False:
            sent_text += f"{all_data['item_model_number']}, {all_data['item_mfr']}, {all_data['brand']}, {all_data['ship_from']}, {all_data['sold_by']}, {item_appliance.title()}, ,{all_data['asin']}, {all_data['price']}, {URL}, "
    item_webpage.close()
     # attempts to run the program twice since some user agents might not be working and want to make sure we get all the information from Amazon
    if (isFirstAttempt):
        sleep(0.5)
        return handle_csv(URL, item_appliance, count_products, False, has_headers)
    else:   
        return sent_text, count_products, all_data["prod_title"]

