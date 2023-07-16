import mysql.connector
import json
import pandas as pd
import os

from django.shortcuts import render, redirect, HttpResponse
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import auth
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.utils import IntegrityError
from django.apps import apps
from django.http import FileResponse

from .decorators import unauthenticated_user
from . import algorithm
from .models import create_dynamic_model
from user.views import export_table_to_excel

MyTable = None


def get_latest_sno(model_name, app_label):
    """Helper Function to get serial number"""
    model = create_dynamic_model(model_name, app_label)
    latest_obj = model.objects.latest('S_No')
    return latest_obj.S_No


"""Connection with DB"""
cnx = mysql.connector.connect(
    user='rciuser', password='Rci@user$1234', host='localhost', database='rcidb')
cursor = cnx.cursor()

cnx_log = mysql.connector.connect(
    user='rciuser', password='Rci@user$1234', host='localhost', database='rcidb_logs')
cursor_log = cnx_log.cursor()


@unauthenticated_user
def login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        user = auth.authenticate(request, username=username, password=password)

        if user is not None:
            if username[0] == 'A':
                auth.login(request, user)
                return redirect('main:select_table')
            elif username[0] == 'U':
                return redirect('user:dataDownload')
        else:
            messages.info(
                request, 'Incorrect username and password')
            return render(request, 'login.html')
    return render(request, 'main/login.html')


def logout(request):
    auth.logout(request)
    return redirect('main:login')


@login_required(login_url='/login')
def selectTable(request):
    context = {}

    # Run a SQL query to get all tables
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
    actualTables = [table[0]
                    for table in allTables if table[0] not in excludedTables]
    context['tables'] = actualTables

    # try:
    if 'submit' in request.GET:
        if request.GET['newTable'] and request.GET['existingTable']:
            """Display error"""
            messages.info(
                request, 'Please select a new table or create a new table')
        elif request.GET['existingTable']:
            """Store table name in a variable and use it next page while inserting data"""
            tableName = request.GET['existingTable']
            request.session['table_name'] = tableName

            return redirect('main:dataentry')
        elif request.GET['newTable']:
            """Create a new table in rcidb, store in a variable and use in next page while inserting data, NO"""
            tableName = request.GET['newTable']
            request.session['table_name'] = tableName

            if tableName not in actualTables:
                cursor.execute(f"CREATE TABLE IF NOT EXISTS {tableName} (S_No INT PRIMARY KEY, Parameter_Name VARCHAR(20) NOT NULL, Command_Word VARCHAR(20) NOT NULL, Word_No INT NOT NULL, Word_Length INT NOT NULL, Scale FLOAT NOT NULL, Units VARCHAR(20) NOT NULL, Data_Type VARCHAR(20) NOT NULL, Para_1 VARCHAR(100) NOT NULL, Para_2 VARCHAR(100) NOT NULL, Endian VARCHAR(20) NOT NULL)")
                # algorithm.writeLog(cursor_log, tableName,
                #                    f"Table {tableName} created")
                # cnx_log.commit()  # committing changes to log table

                return redirect('main:dataentry')
            else:
                messages.info(request, f'ICD with {tableName} already exists')
                return redirect('main:select_table')
        else:
            messages.info(
                request, 'Select a table or create a new table to proceed further')
    elif 'download' in request.GET:
        if request.GET['newTable']:
            messages.info(
                request, f'Select an existing ICD to download data.')
        elif request.GET['existingTable']:
            # convert data in table to excel and download in user's pc
            tableName = request.GET['existingTable']
            export_table_to_excel(tableName, tableName+'.xlsx')
            # download the file
            file_path = os.path.join('excelfiles', f'{tableName}.xlsx')
            response = FileResponse(open(file_path, 'rb'))
            response['content_type'] = 'application/vnd.ms-excel'
            response['Content-Disposition'] = f'attachment; filename="{tableName}.xlsx"'

            # delete the file from the server
            if os.path.exists(path=file_path):
                os.remove(path=file_path)

            return response
        else:
            messages.info(
                request, f'Select an existing ICD to download data.')
    elif 'delete_table' in request.GET:
        table_name = request.GET['existingTable']
        return redirect(f'delete_table/{table_name}')
    # except:
    #     messages.info(request, 'Some error occurred')

    return render(request, 'main/tableSelection.html', context)


@login_required(login_url='/login')
def dataEntry(request):
    tableName = request.session.get('table_name')

    # generating a model for the selected table
    global MyTable
    MyTable = create_dynamic_model(tableName, 'main')

    if MyTable is None:
        MyTable = create_dynamic_model(tableName, 'main')

    if tableName is None:
        return redirect('main:select_table')
    else:
        try:
            s_no = get_latest_sno(tableName, 'main') + 1
        except:
            s_no = 1

        context = {'table_name': tableName, 's_no': s_no}
        context['data'] = MyTable.objects.all()

        if request.method == 'POST':
            try:
                parameter_name = request.POST['parameter']
                command_word = request.POST['command']
                word_no = request.POST['word_no']
                word_length = request.POST['word_length']
                scale = request.POST['scale']
                units = request.POST['units']
                data_type = request.POST['data_type']
                parameter1 = request.POST['para1']
                parameter2 = request.POST['para2']
                endian = request.POST['endian']
            except:
                messages.info(request, 'Enter data in all the fields')

            res = algorithm.check_and_validate(
                param_name=parameter_name, command_word=command_word, word_num=word_no, word_length=word_length, scale=scale, units=units)

            if res == True:
                try:
                    # Create and insert new instance of the model
                    my_table = MyTable(S_No=s_no, Parameter_Name=parameter_name, Command_Word=command_word, Word_No=word_no, Word_Length=word_length,
                                       Scale=scale, Units=units, Data_Type=data_type, Para_1=parameter1, Para_2=parameter2, Endian=endian)
                    my_table.save()

                    context['success_message'] = 'Data Entered Successfully'
                    messages.success(
                        request, 'Data has been successfully added to the table.')
                except IntegrityError as e:
                    messages.info(request, f'SQL Error: {e}')
                return redirect('main:dataentry')
            elif res == False:
                # Display error message
                messages.info(
                    request, "Error in command word validation, recheck word number, word length and command word before reentering.")
            else:
                # display error message
                messages.info(request, res)

    return render(request, 'main/dataEntry.html', context)


def update_data(request, serial_number):
    tableName = request.session.get('table_name')
    global MyTable
    if MyTable is None:
        MyTable = create_dynamic_model(tableName, 'main')
    data = MyTable.objects.get(S_No=serial_number)

    context = {'table_name': tableName, 's_no': serial_number}
    if request.method == 'POST':
        try:
            parameter_name = request.POST['parameter']
            command_word = request.POST['command']
            word_no = request.POST['word_no']
            word_length = request.POST['word_length']
            scale = request.POST['scale']
            units = request.POST['units']
            data_type = request.POST['data_type']
            parameter1 = request.POST['para1']
            parameter2 = request.POST['para2']
            endian = request.POST['endian']
        except:
            messages.info(request, 'Enter data in all the fields')

        res = algorithm.check_and_validate(
            param_name=parameter_name, command_word=command_word, word_num=word_no, word_length=word_length, scale=scale, units=units)
        try:
            if res == True:
                data.Parameter_Name = request.POST.get('parameter')
                data.Command_Word = request.POST.get('command')
                data.Word_No = request.POST.get('word_no')
                data.Word_Length = request.POST.get('word_length')
                data.Scale = request.POST.get('scale')
                data.Units = request.POST.get('units')
                data.Data_Type = request.POST.get('data_type')
                data.Para_1 = request.POST.get('para1')
                data.Para_2 = request.POST.get('para2')
                data.Endian = request.POST.get('endian')
                data.save()
                return redirect('main:dataentry')
            elif res == False:
                # Display error message
                messages.info(
                    request, "Error in command word validation, recheck word number, word length and command word before reentering.")
            else:
                # display error message
                messages.info(request, res)
        except Exception as e:
            messages.info(request, f'SQL Error: {e}')

    return render(request, 'main/update.html', context)


def delete_data(request, serial_number):
    tableName = request.session.get('table_name')
    global MyTable
    if MyTable is None:
        MyTable = create_dynamic_model(tableName, 'main')
    data = MyTable.objects.get(S_No=serial_number)
    data.delete()

    messages.success(request, 'Data deleted successfully')
    return redirect('main:dataentry')


def delete_table(request, table_name):
    if request.method == 'POST':
        if 'yes' in request.POST:
            # delete table
            query = f'DROP TABLE {table_name}'

            global cursor
            cursor.execute(query)
            messages.success(request, f'ICD {table_name} deleted successfully')
            return redirect('main:select_table')
        elif 'no' in request.POST:
            # redirect to table selection page
            return redirect('main:select_table')
    return render(request, 'main/deleteTable.html', {'table_name': table_name})
