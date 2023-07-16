from django import forms
from .models import create_dynamic_model


tableName = request.session.get('table_name')
MyTable = models.create_dynamic_model(tableName, 'main')

class UpdateForm(forms.ModelForm):
    class Meta:
        model = MyTable
        fields = [
            'Parameter_Name', 'Command_Word', 'Word_No', 'Word_Length', 'Scale', 'Units', 'Data_Type', 'Para_1', 'Para_2', 'Endian'
        ]
