import re
from .models import create_dynamic_model
import pandas as pd

from django.http import HttpResponse
from django.db import connection

def writeLog(cursor, table_name, change_made):
    """Function to write LOG"""
    cursor.execute(
        f"INSERT INTO {table_name+'_log'} (Changes_made, Change_time) values (\'{change_made}\',NOW())")


def check_and_validate(param_name, command_word, word_num, word_length, scale, units):
    errors = []
    if len(param_name) >= 10:
        errors.append("Parameter name should be less than 10 characters")
    if not re.match("^[0-9a-fA-F]{4}$", command_word):
        errors.append("Command Word should be a valid 4-digit hex number")
    try:
        if int(word_num) > 32 or int(word_length) > 32:
            errors.append(
                "Word Number and Word Length should not be more than 32")
    except ValueError:
        errors.append("Word Number and Word Length should be integers")
    try:
        if '.' in scale and len(scale.split(".")[1]) > 6:
            errors.append("Scale should not have more than 6 decimal points")
    except ValueError:
        errors.append("Scale should be a decimal number")
    if len(units) >= 5:
        errors.append("Units should be less than 5 characters")
    if len(errors) == 0:
        last_5_bits = int(command_word, 16) & 0x1F
        if last_5_bits == 0:
            last_5_bits = 32
        if (int(word_num) + int(word_length)) < last_5_bits:
            # return "Inputs are valid and passed the check_command_word function"
            return True
        else:
            # return "Inputs are valid but failed the check_command_word function"
            return False
    else:
        return "\n".join(errors)


def export_data(request, table_name, app_label):
    # Get the data from the SQL table
    with connection.cursor() as cursor:
        cursor.execute(f"SELECT * FROM {table_name}")
        data = cursor.fetchall()

    # Convert the data to a pandas dataframe
    df = pd.DataFrame(data)

    # Create an HttpResponse object with the Excel file
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename={table_name}.xlsx'

    # Save the dataframe to the response object
    df.to_excel(response, index=False)

    return response
