from django.db import models
from django.utils.translation import ugettext_lazy as _

from pretix.base.models import Team


class CasAttributeTeamAssignmentRule(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    attribute = models.CharField(max_length=100, verbose_name=_('CAS attribute'))

    class Meta:
        verbose_name = _('Team assignment rule')
