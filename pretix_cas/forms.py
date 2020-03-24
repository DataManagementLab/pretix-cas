from django.forms import ModelForm

from .models import CasAttributeTeamAssignmentRule


class CasAssignmentRuleForm(ModelForm):
    def __init__(self, organizer, *args, **kwargs):
        super(CasAssignmentRuleForm, self).__init__(*args, **kwargs)
        self.fields['team'].queryset = self.fields['team'].queryset.filter(organizer=organizer)

    class Meta:
        model = CasAttributeTeamAssignmentRule
        fields = ['team', 'attribute']
