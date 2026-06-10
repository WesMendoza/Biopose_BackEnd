import os
import re

sql_path = r"D:\Daniel\Actividades\Python\Proyecto BIOPOSE\Biopose_BackEnd\backend\scripts\db\create\CreateDb.sql"
models_path = r"D:\Daniel\Actividades\Python\Proyecto BIOPOSE\Biopose_BackEnd\backend\apps\analysis\models.py"

# --- Fix CreateDb.sql ---
with open(sql_path, "r", encoding="utf-8") as f:
    sql_content = f.read()

# We want to wrap camelCase words in double quotes if they aren't already wrapped.
# But we must be careful with types (VARCHAR), keywords (CREATE TABLE), etc.
# A safe approach is to find all declarations and wrap them.
# The user wants tables and columns.
# Let's use a regex that matches camelCase (e.g. idEmpresa, menuOption)
def quote_camel(match):
    word = match.group(0)
    # Don't quote if already quoted, or if it's all upper
    if word.isupper(): return word
    return f'"{word}"'

# Words that start with lowercase and have at least one uppercase letter
camel_pattern = re.compile(r'\b[a-z]+[A-Z][a-zA-Z0-9]*\b')

lines = sql_content.split('\n')
new_lines = []
for line in lines:
    # skip some lines like comments
    if line.strip().startswith("--") or line.strip().startswith("SET") or line.strip().startswith("CREATE SCHEMA"):
        new_lines.append(line)
        continue
    
    # We don't want to quote things inside single quotes (strings)
    # For simplicity, if there's no single quote, apply to camelCase words
    if "'" not in line:
        line = camel_pattern.sub(quote_camel, line)
    else:
        # split by single quotes to avoid quoting inside string literals
        parts = line.split("'")
        for i in range(0, len(parts), 2):
            parts[i] = camel_pattern.sub(quote_camel, parts[i])
        line = "'".join(parts)
    new_lines.append(line)

with open(sql_path, "w", encoding="utf-8") as f:
    f.write("\n".join(new_lines))


# --- Fix models.py ---
with open(models_path, "r", encoding="utf-8") as f:
    models_content = f.read()

# We want to change db_column='idimageupload' to db_column='idImageUpload'
# Because we know the field names exactly match the camelCase names, 
# we can look for "field_name = models.FieldType(..., db_column='something')"
# and replace 'something' with the field_name!

new_models_lines = []
for line in models_content.split('\n'):
    if "db_column=" in line and "=" in line:
        # e.g., idEmpresa = models.IntegerField(null=True, blank=True, db_column='idempresa')
        field_name_match = re.match(r'^\s*([a-zA-Z0-9_]+)\s*=', line)
        if field_name_match:
            field_name = field_name_match.group(1)
            # Find the db_column='...' part and replace it
            line = re.sub(r"db_column='[^']*'", f"db_column='{field_name}'", line)
            line = re.sub(r'db_column="[^"]*"', f'db_column="{field_name}"', line)
    
    # For db_table
    if "db_table =" in line or "db_table=" in line:
        if 'analysisimageupload' in line:
            line = line.replace('analysisimageupload', 'analysisImageUpload')
        elif 'analysisvideoupload' in line:
            line = line.replace('analysisvideoupload', 'analysisVideoUpload')
        elif 'analysisdetectionevent' in line:
            line = line.replace('analysisdetectionevent', 'analysisDetectionEvent')
        elif 'analysispersonkeypoints' in line:
            line = line.replace('analysispersonkeypoints', 'analysisPersonKeypoints')
        elif 'analysisreport' in line:
            line = line.replace('analysisreport', 'analysisReport')
        elif 'systemParameter' in line:
            line = line.replace('systemParameter', 'systemParameter') # unchanged
    new_models_lines.append(line)

with open(models_path, "w", encoding="utf-8") as f:
    f.write("\n".join(new_models_lines))

print("Case fix completed!")
