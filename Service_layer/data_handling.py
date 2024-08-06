from utils.config import logger
import os
import pdfplumber

def extract_text_from_pdf(file_path):
    try:
        text = ""
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                text += page.extract_text() + "\n"
        return text
    except Exception as e:
        logger.error(f"Error reading PDF file {file_path}: {e}")
        raise

def fetch_from_files(file_path):
    try:
        data = []
         # Normalize path
        file_path = os.path.abspath(file_path)

        if os.path.isfile(file_path):
            #process single file
            if file_path.lower().endswith('.pdf'):
                # Read PDF file
                content = extract_text_from_pdf(file_path)
                data.append({"data": content, "source": f"File: {os.path.basename(file_path)}"})
            else:
              with open(file_path,'r') as file:
                 content = file.read()
                 data.append({"data": content, "source": f"File: {os.path.basename(file_path)}"})

        elif os.path.isdir(file_path):
            #process ALL files in a directory
            files = os.listdir(file_path)
            for file_name in files:
                full_file_path = os.path.join(file_path, file_name)
                if os.path.isfile(full_file_path):
                    if full_file_path.lower().endswith('.pdf'):
                        # Read PDF file
                        content = extract_text_from_pdf(full_file_path)
                    else:

                      with open(full_file_path,'r') as file:
                        content = file.read()
                        data.append({"data": content, "source": f"File: {file_name}"})
                        
        print("successfully fetch data from file")
        return data
    except Exception as e:
        logger.error(f"Error reading files from {file_path}: {e}")
        raise
    



