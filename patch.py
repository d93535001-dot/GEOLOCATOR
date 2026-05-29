with open('backend_cis.py', 'r') as f:
    content = f.read()

content = content.replace('temp_path = f"temp/{file.filename}"', 'import uuid\n    temp_path = f"temp/{uuid.uuid4().hex}_{file.filename.split(\'/\')[-1].split(\'\\\\\')[-1]}"')

with open('backend_cis.py', 'w') as f:
    f.write(content)
