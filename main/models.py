from django.db import models


def create_dynamic_model(name, app_label):
    if name is None:
        raise ValueError("Model name cannot be None")

    attrs = {
        '__module__': '__main__',
        'Meta': type('Meta', (object,), {'db_table': name, 'app_label': app_label}),
        'S_No': models.IntegerField(primary_key=True),
        'Parameter_Name': models.CharField(max_length=20),
        'Command_Word': models.CharField(max_length=20),
        'Word_No': models.IntegerField(),
        'Word_Length': models.IntegerField(),
        'Scale': models.FloatField(),
        'Units': models.CharField(max_length=20),
        'Data_Type': models.CharField(max_length=20),
        'Para_1': models.CharField(max_length=100),
        'Para_2': models.CharField(max_length=100),
        'Endian': models.CharField(max_length=20),
    }

    model = type(name, (models.Model,), attrs)
    return model
