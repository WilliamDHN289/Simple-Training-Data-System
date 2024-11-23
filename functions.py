import numpy as np
import re
from collections import Counter
import math
import hashlib
import mysql.connector



############################################## Functions for Both Data Loader and Data Accepter ##############################################
"""Calculate hash passwords"""
def hash_password(password):
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

"""verify the log-in information"""
def verify_user(username, password):
    try:
        exact_hash = hash_password(password)

        cursor.execute("SELECT password_hash FROM data_loader WHERE username = %s", (username,))
        loader_result = cursor.fetchone()  
        if loader_result is not None:
            loader_hash = loader_result[0]
        else:
            loader_hash = ''
        
        cursor.execute("SELECT password_hash FROM data_accepter WHERE username = %s", (username,))
        accepter_result = cursor.fetchone()  
        if accepter_result is not None:
            accepter_hash = accepter_result[0]
        else:
            accepter_hash = ''

    
        if exact_hash == loader_hash:
            print(f"Data Loader {username} logged in")
            return 1
        
        elif exact_hash == accepter_hash:
            print(f"Data Accepter {username} logged in")
            return 2

        else:
            print(f"Invalid username or password for {username}")
            return 0
        
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return 0
    
"""Check the data information (Data Loader and Data Accepter)"""
def call_data_statistics():
    try:
        cursor.callproc('get_data_statistics')
        for result in cursor.stored_results():
            rows = result.fetchall()
            for row in rows:
                print(row[0])  

    except mysql.connector.Error as e:
        print(f"Error: {e}")


############################################## Functions for Data Loader ##############################################
"""Calculate cosine similarity between two texts by tokenizing them into words (Data Loader)"""
def calculate_cosine_similarity(content1, content2):
    
    # Tokenize contents into words
    words1 = re.findall(r'\b\w+\b', content1.lower())
    words2 = re.findall(r'\b\w+\b', content2.lower())
    
    # Calculate word frequency (term frequency) for both contents
    freq1 = Counter(words1)
    freq2 = Counter(words2)
    
    # Get the unique set of words in both contents
    all_words = set(freq1.keys()).union(set(freq2.keys()))
    
    # Create vectors for both contents based on term frequency
    vec1 = [freq1[word] for word in all_words]
    vec2 = [freq2[word] for word in all_words]
    
    # Calculate cosine similarity
    dot_product = sum(v1 * v2 for v1, v2 in zip(vec1, vec2))
    magnitude1 = math.sqrt(sum(v ** 2 for v in vec1))
    magnitude2 = math.sqrt(sum(v ** 2 for v in vec2))
    
    if magnitude1 == 0 or magnitude2 == 0:
        return 0.0
    return dot_product / (magnitude1 * magnitude2)
        

"""Upload the new data with seed filter (Data Loader)"""
def process_content_with_seed_filter(content, threshold=0.2):
    # Step 1: Calculate md5_id hash
    md5_id = hashlib.md5(content.encode('utf-8')).hexdigest()
    
    # Check for duplicate content by calling get_combined_md5_ids
    cursor.callproc('get_combined_md5_ids')
    existing_md5_ids = [row[0] for result in cursor.stored_results() for row in result.fetchall()]
    
    if md5_id in existing_md5_ids:
        print("Repeated content")
        return

    # Step 2: Compute cosine similarity scores with seed data categories
    scores = {}
    categories = ["history", "finance", "physics", "chemistry"]
    
    for category in categories:
        cursor.callproc(f'get_{category}_contents')
        seed_contents = [row[0] for result in cursor.stored_results() for row in result.fetchall()]
        
        # Calculate average cosine similarity for this category
        if seed_contents:
            similarities = [calculate_cosine_similarity(content, seed_content) for seed_content in seed_contents]
            scores[category] = sum(similarities) / len(similarities)
        else:
            scores[category] = 0.0  # No seed data for this category

        print(f"Score of {category} is: {scores[category]}")

    # Assign scores to specific variables for upload
    history_score = scores["history"]
    finance_score = scores["finance"]
    physics_score = scores["physics"]
    chemistry_score = scores["chemistry"]

    # Step 3: Determine the best matching category
    best_category = max(scores, key=scores.get)
    if scores[best_category] < threshold:
        print("Doesn't fit any category")
        return

    # Update flags based on the selected category
    flag_values = {"history": 0, "finance": 0, "physics": 0, "chemistry": 0}
    flag_values[best_category] = 1

    
    # Step 4: Upload data using upload_data procedure
    cursor.callproc(
        'upload_data',
        (
            None,  
            content,
            md5_id,
            flag_values["history"],
            flag_values["finance"],
            flag_values["physics"],
            flag_values["chemistry"],
            best_category,
            'seeds',  # filter_method
            history_score,
            finance_score,
            physics_score,
            chemistry_score
        )
    )
    
    # Commit changes
    conn.commit()
    print(f"Data inserted successfully with category: {best_category}")


"""Calculate the keyword matching score based on presence of category keywords in content (Data Loader)"""  
def calculate_keyword_score(content, category_keywords):
    
    words = re.findall(r'\b\w+\b', content.lower())
    unique_words = set(words)
    keyword_matches = [kw for kw in category_keywords if kw in unique_words]
    return len(keyword_matches) / len(category_keywords)


"""Upload the new data with keywords filter (Data Loader)"""
def process_content_with_keywords_filter(content, threshold=0.2):
    # Step 1: Calculate md5_id hash
    md5_id = hashlib.md5(content.encode('utf-8')).hexdigest()
    
    # Check for duplicate content by calling get_combined_md5_ids
    cursor.callproc('get_combined_md5_ids')
    existing_md5_ids = [row[0] for result in cursor.stored_results() for row in result.fetchall()]
    
    if md5_id in existing_md5_ids:
        print("Repeated content")
        return

    # Step 2: Compute keyword scores for each category
    scores = {
        "history": calculate_keyword_score(content, keywords["history"]),
        "finance": calculate_keyword_score(content, keywords["finance"]),
        "physics": calculate_keyword_score(content, keywords["physics"]),
        "chemistry": calculate_keyword_score(content, keywords["chemistry"])
    }

    # Assign scores to specific variables for upload
    history_score = scores["history"]
    finance_score = scores["finance"]
    physics_score = scores["physics"]
    chemistry_score = scores["chemistry"]

    for category in ["history", "finance", "physics", "chemistry"]:
        print(f"Score of {category} is: {scores[category]}")
    
    # Step 3: Determine the best matching category
    best_category = max(scores, key=scores.get)
    if scores[best_category] < threshold:
        print("Doesn't fit any category")
        return
    
    # Update flags based on the selected category
    flag_values = {"history": 0, "finance": 0, "physics": 0, "chemistry": 0}
    flag_values[best_category] = 1

    # Step 5: Upload data using upload_data procedure
    cursor.callproc(
        'upload_data',
        (
            None,  # input_data_id
            content,
            md5_id,
            flag_values["history"],
            flag_values["finance"],
            flag_values["physics"],
            flag_values["chemistry"],
            best_category,
            'keywords',  # filter_method
            history_score,
            finance_score,
            physics_score,
            chemistry_score
        )
    )
    
    # Commit changes
    conn.commit()
    print(f"Data inserted successfully with category: {best_category}")


"""Delete data (Data Loader)"""
def delete_data(data_id):
    try:
        cursor.callproc('delete_data_by_id', [data_id])
        conn.commit()  
        print(f"Data with data_id {data_id} has been deleted successfully.")
    except mysql.connector.Error as e:
        print(f"Error: {e}")


############################################## Functions for Data Accepter ##############################################
"""Check the data information log"""
def get_data_info(data_id):
    try:
        cursor.callproc('get_data_info', [data_id])
        for result in cursor.stored_results():
            rows = result.fetchall()
            for row in rows:
                print("Data ID:", row[0])
                print("Content:", row[1])
                print("MD5 ID:", row[2])
                print("Category:", row[3])
                print("Filter Method:", row[4])
                print("History Score:", row[5])
                print("Finance Score:", row[6])
                print("Physics Score:", row[7])
                print("Chemistrt Score:", row[8])
                print("------")

    except mysql.connector.Error as e:
        print(f"Error: {e}")


"""Retrieve the specific training data"""
def get_training_data(data_id):
    try:
        cursor.callproc('get_training_data_by_id', [data_id])
        result_data = []
        for result in cursor.stored_results():
            rows = result.fetchall()
            for row in rows:
                data = {
                    "Data ID": row[0],
                    "Content": row[1],
                    "MD5 ID": row[2],
                    "History Flag": row[3],
                    "Finance Flag": row[4],
                    "Physics Flag": row[5],
                    "Chemistry Flag": row[6]
                }
                result_data.append(data)

        return result_data  

    except mysql.connector.Error as e:
        print(f"Error: {e}")
        return None
    

"""Retrieve data with high quality"""
def get_high_quality_data(threshold=0.4):
    try:
        cursor.callproc('GetHighScoreDataIds', (threshold,))
        data_ids = []
        for result in cursor.stored_results():
            data_ids = [row[0] for row in result.fetchall()]
        
        if not data_ids:
            return {}
        
        data_content = {}
        for data_id in data_ids:
            col_name = "data_id " + str(data_id)
            cursor.callproc('get_training_data_by_id', (data_id,))
            for result in cursor.stored_results():
                row = result.fetchone()
                if row:
                    data_content[col_name] = row[1]
        
        return data_content

    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None


"""Retrieve data with low quality"""
def get_low_quality_data(threshold=0.3):
    try:
        cursor.callproc('GetLowScoreDataIds', (threshold,))
        
        data_ids = []
        for result in cursor.stored_results():
            data_ids = data_ids = [row[0] for row in result.fetchall()]
        
        if not data_ids:
            return {}
        
        data_content = {}
        for data_id in data_ids:
            col_name = "data_id " + str(data_id)
            cursor.callproc('get_training_data_by_id', (data_id,))
            for result in cursor.stored_results():
                row = result.fetchone()
                if row:
                    data_content[col_name] = row
        
        return data_content

    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None
    
"""Generate new seed data"""
def add_seed_data(data_id):
    try:
        cursor.callproc('AddSeedData', [data_id])
        conn.commit()
        print(f"Seed data for data_id {data_id} has been added successfully.")

        cursor.execute("SELECT COUNT(data_id) AS max_data_id FROM seed_data;")
        result = cursor.fetchone()
        max_data_id = result[0] if result else 0
        
        print(f"Current number of seed data: {max_data_id}")
    except mysql.connector.Error as err:
        print(f"Error: {err}")

"""Delete special seed data"""
def delete_seed_data(data_id):
    try:
        cursor.callproc('DeleteSeedData', [data_id])
        conn.commit()
        print(f"Seed data with data_id {data_id} has been deleted successfully.")

        cursor.execute("SELECT COUNT(data_id) AS max_data_id FROM seed_data;")
        result = cursor.fetchone()
        max_data_id = result[0] if result else 0
        
        print(f"Current number of seed data: {max_data_id}")
    except mysql.connector.Error as err:
        print(f"Error: {err}")


if __name__ == "__main__":
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="P@ss8107",
        database="CSC3170"
    )
    cursor = conn.cursor()

    keywords = {
        "history": ["history", "ancient", "war", "empire", "civilization", "revolution", "dynasty", "colonial", "medieval", "archaeology"],
        "finance": ["finance", "economy", "investment", "market", "stock", "currency", "capital", "inflation", "trade", "bank"],
        "physics": ["physical", "quantum", "energy", "force", "particle", "motion", "relativity", "gravity", "wave", "thermodynamics"],
        "chemistry": ["chemical", "molecule", "reaction", "compound", "acid", "base", "organic", "element", "catalyst", "bond"]
    }

    username = input("Please enter your username:")
    password = input("Please enter your passwords:")
    log_verify = verify_user(username, password)

    if log_verify == 1:
        while True:
            job = input("Please choose your action, 0: Exit, 1: Statistic checking, 2: Upload with seed filter, 3: Upload with keywords filter, 4: Delete:")
            print('------------------------------------------------------------')
            if job == "0":
                print(f"Goodbye {username}")
                break
            elif job == "1":
                call_data_statistics()
            elif job == "2":
                content = input("Please enter your input content:")
                process_content_with_seed_filter(content)
            elif job == "3":
                content = input("Please enter your input content:")
                process_content_with_keywords_filter(content)
            elif job == "4":
                data_id = int(input("Please enter the deleted data id:"))
                delete_data(data_id)
            else:
                print("Wrong action!")
            print('------------------------------------------------------------')
                
    elif log_verify == 2:
        while True:
            job = input("Please choose your action, 0: Exit, 1: Statistic checking, 2: Information checking, 3: Retrieve data, 4: Retrieve high-quality data, 5: Retrieve low-quality data, 6: Generate new seed, 7: Delete seed:")
            print('------------------------------------------------------------')
            if job == "0":
                print(f"Goodbye {username}")
                break
            elif job == "1":
                call_data_statistics()
            elif job == "2":
                data_id = int(input("Please enter the checking data id:"))
                get_data_info(data_id)
            elif job == "3":
                data_id = int(input("Please enter the retrieveing data id:"))
                data = get_training_data(data_id)
                print(f"Already get data {data}")
            elif job == "4":
                high_data = get_high_quality_data()
                if high_data:
                    print(f"Already get high-quality data {high_data}")
                else:
                    print("No high-quality data")
            elif job == "5":
                low_data = get_low_quality_data()
                if low_data:
                    print(f"Already get low-quality data {high_data}")
                else:
                    print("No low-quality data")
            elif job == "6":
                data_id = int(input("Please enter the data id to add into seed:"))
                add_seed_data(data_id)
            elif job == "7":
                data_id = int(input("Please enter the deleting seed id:"))
                delete_seed_data(data_id)
            else:
                print("Wrong action!")
            print('------------------------------------------------------------')


    
    cursor.close()
    conn.close()