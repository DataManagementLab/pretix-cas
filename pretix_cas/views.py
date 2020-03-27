import cas
from django.conf import settings
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _
from django.views.generic import TemplateView
from django.views.generic.edit import CreateView, DeleteView, UpdateView

from pretix.base.models import Team, User
from pretix.control.permissions import OrganizerPermissionRequiredMixin
from pretix.control.views.auth import process_login
from pretix.helpers.urls import build_absolute_uri

from . import auth_backend
from .forms import CasAssignmentRuleForm
from .models import CasAttributeTeamAssignmentRule


def return_from_sso(request):
    """
    This function will be called when the user returns from the CAS server, presenting the ticket of the CAS server.
    """
    cas_response = __verify_cas(request)

    # If the ticket could not be verified, the response is {None, None, None}
    if cas_response[0] is None:
        return HttpResponse(_('Login failed'))
    else:
        # See __create_new_user_from_cas_data for data format
        email = cas_response[1]['mail']
        try:
            user = User.objects.filter(email=email).get()
        except ObjectDoesNotExist:
            locale = request.LANGUAGE_CODE if hasattr(request, 'LANGUAGE_CODE') else settings.LANGUAGE_CODE
            timezone = request.timezone if hasattr(request, 'timezone') else settings.TIME_ZONE
            user = __create_new_user_from_cas_data(cas_response, locale, timezone)

        if user.auth_backend != auth_backend.CasAuthBackend.identifier:
            return HttpResponseBadRequest(_('Could not create user: Email is already registered.'))

        group_membership = cas_response[1].get('groupMembership')
        ou = cas_response[1].get('ou')
        __add_user_to_teams(user, group_membership, ou)

        return process_login(request, user, False)


def __verify_cas(request):
    # This is the absolute URL of the view that receives the ticket from the client (generated by the CAS Server).
    return_address = build_absolute_uri('plugins:pretix_cas:cas.response')

    # The CASClient is created on every request because the domain of the pretix instance is not fixed.
    cas_client = cas.CASClient(
        version='CAS_2_SAML_1_0',
        server_url='https://sso.tu-darmstadt.de',
        service_url=return_address
    )
    ticket = request.GET.get('ticket')
    # Validate ticket with CAS Server, receive user information.
    return cas_client.verify_ticket(ticket)


class AssignmentRulesList(TemplateView, OrganizerPermissionRequiredMixin):
    """
    This view renders the team assignment rules settings page.
    """
    template_name = 'pretix_cas/cas_assignment_rules.html'
    permission = 'can_change_organizer_settings'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        organizer = self.request.organizer
        context['teams'] = Team.objects.filter(organizer=organizer)
        context['assignmentRules'] = CasAttributeTeamAssignmentRule.objects.filter(team__organizer=organizer)
        return context


class AssignmentRuleEditMixin(OrganizerPermissionRequiredMixin):
    model = CasAttributeTeamAssignmentRule
    permission = 'can_change_organizer_settings'

    def get_success_url(self):
        return reverse('plugins:pretix_cas:team_assignment_rules',
                       kwargs={'organizer': self.request.organizer.slug})


class AssignmentRuleUpdateMixin(AssignmentRuleEditMixin):
    fields = ['team', 'attribute']
    template_name = 'pretix_cas/cas_assignment_rule_edit.html'

    def get_form(self, form_class=None):
        return CasAssignmentRuleForm(organizer=self.request.organizer, **self.get_form_kwargs())

    def form_valid(self, form):
        super().form_valid(form)
        messages.success(self.request, _('The new assignment rule has been created.'))
        return redirect(self.get_success_url())

    def form_invalid(self, form):
        messages.error(self.request, _('The assignment rule could not be created.'))
        return super().form_invalid(form)


class AssignmentRuleCreate(AssignmentRuleUpdateMixin, CreateView):
    """
    This view enables the organizer to add a new team assignment rule.
    """


class AssignmentRuleEdit(AssignmentRuleUpdateMixin, UpdateView):
    """
    This view enables the organizer to update an existing team assignment rule.
    """


class AssignmentRuleDelete(AssignmentRuleEditMixin, DeleteView):
    """
    This view enables the organizer to delete an existing team assignment rule.
    """
    template_name = 'pretix_cas/cas_assignment_rule_delete.html'


def __create_new_user_from_cas_data(cas_response, locale, timezone):
    """
    Creates a user from the fields in the CAS payload.
    :param cas_response: The payload that is returned by CAS.
    :param locale: The locale for the new user.
    :param timezone:  The timezone for the new user.
    :return: The user model that was created.
    """
    # On successful verification the returned triple looks something like this:
    # ('ab12abcd',
    #   {'mail': 'john.doe@tu-darmstadt.de', 'eduPersonAffiliation': ['student', 'member', 'employee'],
    #    'ou': ['T20', 'FB20'], 'groupMembership': ['cn=T20', 'ou=central-it', 'o=tu-darmstadt'],
    #    'givenName': 'John', 'successfulAuthenticationHandlers': 'LdapAuthenticationHandler', 'fullName': 'Doe, John',
    #    'tudUserUniqueID': '123456789', 'cn': 'ab12abcd', 'credentialType': 'UsernamePasswordCredential',
    #    'samlAuthenticationStatementAuthMethod': 'urn:oasis:names:tc:SAML:1.0:am:password', 'tudMatrikel': '1234567',
    #    'authenticationMethod': 'LdapAuthenticationHandler', 'surname': 'Doe'
    #   }, None)
    user_info = cas_response[1]
    email = user_info['mail']
    given_name = user_info['givenName']
    surname = user_info['surname']
    fullname = '%s %s' % (given_name, surname)

    created_user = User.objects.create(
        email=email,
        fullname=fullname,
        locale=locale,
        timezone=timezone,
        auth_backend=auth_backend.CasAuthBackend.identifier,
        password='',
    )

    return created_user


def __add_user_to_teams(user, ou_attributes=None, group_membership_attributes=None):
    """
    Assigns users to teams based on the set assignment rules.
    It doesn't matter whether the user is already in the team, or not.

    :param user: The pretix 'User' object of the user that logged in
    :param ou_attributes: The list of ou attributes of the user received by the CAS server
    :param group_membership_attributes: The list of groupMembership attributes of the user received by the CAS server
    """
    # The response from the CAS server can respond with None, an empty list, a single attribute, or a list with
    # attributes
    if ou_attributes is None:
        ou_attributes = []
    if type(ou_attributes) is not list:
        ou_attributes = [ou_attributes]
    if group_membership_attributes is None:
        group_membership_attributes = []
    if type(group_membership_attributes) is not list:
        group_membership_attributes = [group_membership_attributes]

    assignment_rules = CasAttributeTeamAssignmentRule.objects.all()

    teams = {matcher.team for matcher in assignment_rules
             if (matcher.attribute in ou_attributes or matcher.attribute in group_membership_attributes)}

    for team in teams:
        try:
            team.members.add(user)
        except ObjectDoesNotExist:
            pass
