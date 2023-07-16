import mysql.connector
import pandas as pd
import os

from django.shortcuts import render
from django.http import FileResponse


def dataDownload(request):
    context = {}

    connection = mysql.connector.connect(
        host='localhost',
        user='rciuser',
        password='Rci@user$1234',
        database='rcidb'
    )
    cursor = connection.cursor()

    cursor.execute("SHOW TABLES")
    allTables = cursor.fetchall()
    excludedTables = [
        "auth_group",
        "auth_group_permissions",
        "auth_permission",
        "auth_user",
        "auth_user_groups",
        "auth_user_user_permissions",
        "django_admin_log",
        "django_content_type",
        "django_migrations",
        "django_session"
    ]

    cursor.close()
    connection.close()

    actualTables = [table[0]
                    for table in allTables if table[0] not in excludedTables]
    context['tables'] = actualTables

    if request.method == 'POST':
        table_name = request.POST['table_name']
        # call function to generate excel file
        export_table_to_excel(table_name, table_name+'.xlsx')
        # download excel file to user's pc
        file_path = os.path.join('excelfiles', f'{table_name}.xlsx')
        response = FileResponse(open(file_path, 'rb'))
        response['content_type'] = 'application/vnd.ms-excel'
        response['Content-Disposition'] = f'attachment; filename="{table_name}.xlsx"'

        # delete the file from the server
        if os.path.exists(path=file_path):
            os.remove(path=file_path)

        return response

    return render(request, 'user/dataDownload.html', context)


def export_table_to_excel(table_name, excel_file):
    # Connect to the MySQL server
    connection = mysql.connector.connect(
        host='localhost',
        user='rciuser',
        password='Rci@user$1234',
        database='rcidb'
    )

    # Fetch the data from the table
    cursor = connection.cursor()
    cursor.execute(f"SELECT * FROM {table_name}")
    data = cursor.fetchall()

    # Get the column names
    column_names = [i[0] for i in cursor.description]

    # Create a DataFrame from the data
    df = pd.DataFrame(data, columns=column_names)

    # Export the DataFrame to an Excel file
    df.to_excel(f'excelfiles/{excel_file}', index=False)

    # Close the MySQL connection
    cursor.close()
    connection.close()
