from django.urls import path

from . import views

urlpatterns = [
    path('cas_login', views.return_from_sso, name='cas.response'),
    path('^control/organizer/<str:organizer>/teams/assignment_rules', views.AssignmentRulesList.as_view(),
        name='team_assignment_rules'),
    path('control/organizer/<str:organizer>/teams/assignment_rules/add', views.AssignmentRuleCreate.as_view(),
        name='team_assignment_rules.add'),
    path('control/organizer/<str:organizer>/teams/assignment_rules/<int:pk>/edit',
        views.AssignmentRuleEdit.as_view(),
        name='team_assignment_rules.edit'),
    path('control/organizer/<str:organizer>/teams/assignment_rules/<int:pk>/delete',
        views.AssignmentRuleDelete.as_view(),
        name='team_assignment_rules.delete'),
]
