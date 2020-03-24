import pytest
from pretix_cas import views, auth_backend
from pretix_cas.models import CasAttributeTeamAssignmentRule
from rest_framework.reverse import reverse

from pretix.base.models import User, Team, Organizer

fake_cas_data = ('ab12abcd',
                 {'mail': 'john.doe@tu-darmstadt.de', 'eduPersonAffiliation': ['student', 'member', 'employee'],
                  'ou': ['T20', 'FB20'], 'groupMembership': ['cn=T20', 'ou=central-it', 'o=tu-darmstadt'],
                  'givenName': 'John', 'surname': 'Doe'
                  }, None)


def login_mock(cas_data, client):
    # Override verification of the ticket to just return the simply return 'cas_data'
    views.__verify_cas = lambda request: cas_data
    client.get(reverse('plugins:pretix_cas:cas.response'))


def get_user(cas_data):
    return User.objects.get(email=cas_data[1].get('mail'))


def is_part_of_team(user, team):
    return user.teams.filter(id=team.id).exists()


@pytest.fixture
def env():
    organizer = Organizer.objects.create(name="FB 20", slug="FB20")
    central_it_team = Team.objects.create(name="Central IT", organizer=organizer, can_view_orders=True)
    admin_team = Team.objects.create(name="Admins", organizer=organizer, can_change_event_settings=True)
    employee_team = Team.objects.create(name="Employees", organizer=organizer, can_view_vouchers=True)
    return central_it_team, admin_team, employee_team


@pytest.mark.django_db
def test_successful_user_creation(env, client):
    login_mock(fake_cas_data, client)
    created_user = get_user(fake_cas_data)
    assert created_user.email == fake_cas_data[1]['mail']
    assert created_user.get_full_name() == fake_cas_data[1]['givenName'] + " " + fake_cas_data[1]['surname']
    assert created_user.auth_backend == auth_backend.CasAuthBackend.identifier


@pytest.mark.django_db
def test_failed_user_creation(env, client):
    login_mock((None, None, None), client)
    assert User.objects.count() == 0


@pytest.mark.django_db
def test_login_with_weird_cas_attribute_list_response(env, client):
    team1 = env[0]
    CasAttributeTeamAssignmentRule.objects.create(attribute='FB20', team=team1)
    team2 = env[2]
    CasAttributeTeamAssignmentRule.objects.create(attribute='o=tu-darmstadt', team=team2)

    login_mock(('ab12abcd',
                {'mail': 'abc@def.gh', 'givenName': 'John', 'surname': 'Doe'},
                None), client)

    login_mock(('ab12abcd',
                {'mail': 'abc@def.gh', 'givenName': 'John', 'surname': 'Doe', 'ou':[], 'groupMembership':[]},

                None), client)

    login_mock(('ab12abcd',
                {'mail': 'abc@def.gh', 'givenName': 'John', 'surname': 'Doe', 'ou': None, 'groupMembership': None},
                None), client)

    login_mock(('ab12abcd',
                {'mail': 'abc@def.gh', 'givenName': 'John', 'surname': 'Doe', 'ou': 'FB20', 'groupMembership': None},
                None), client)

    assert is_part_of_team(get_user(('',{'mail': 'abc@def.gh'}, None)), team1)
    assert not is_part_of_team(get_user(('',{'mail': 'abc@def.gh'}, None)), team2)

    login_mock(('ab12abcd',
                {'mail': 'abc@def.gh', 'givenName': 'John', 'surname': 'Doe', 'ou': None, 'groupMembership': 'o=tu-darmstadt'},
                None), client)

    assert is_part_of_team(get_user(('',{'mail': 'abc@def.gh'}, None)), team1)
    assert is_part_of_team(get_user(('',{'mail': 'abc@def.gh'}, None)), team2)


@pytest.mark.django_db
def test_auto_assign_ou_rules(env, client):
    expected_team = env[0]

    CasAttributeTeamAssignmentRule.objects.create(attribute="T20", team=expected_team)

    login_mock(fake_cas_data, client)
    user = get_user(fake_cas_data)

    assert is_part_of_team(user, expected_team)
    assert user.teams.count() == 1


@pytest.mark.django_db
def test_auto_assign_group_membership_rules(env, client):
    central_it_team = env[0]
    admin_team = env[1]
    employee_team = env[2]

    CasAttributeTeamAssignmentRule.objects.create(attribute="ou=central-it", team=central_it_team)
    CasAttributeTeamAssignmentRule.objects.create(attribute="ou=admin", team=admin_team)
    CasAttributeTeamAssignmentRule.objects.create(attribute="cn=T20", team=employee_team)

    login_mock(fake_cas_data, client)
    user = get_user(fake_cas_data)

    assert is_part_of_team(user, central_it_team)
    assert is_part_of_team(user, employee_team)
    assert not is_part_of_team(user, admin_team)
    assert user.teams.count() == 2


@pytest.mark.django_db
def test_auto_assign_both(env, client):
    central_it_team = env[0]
    admin_team = env[1]
    employee_team = env[2]

    CasAttributeTeamAssignmentRule.objects.create(attribute="ou=central-it", team=central_it_team)  # Match
    CasAttributeTeamAssignmentRule.objects.create(attribute="ou=admin", team=admin_team)  # No match

    CasAttributeTeamAssignmentRule.objects.create(attribute="T20", team=employee_team)  # Match
    CasAttributeTeamAssignmentRule.objects.create(attribute="FB00", team=admin_team)  # No match

    login_mock(fake_cas_data, client)
    user = get_user(fake_cas_data)

    assert is_part_of_team(user, central_it_team)
    assert not is_part_of_team(user, admin_team)
    assert is_part_of_team(user, employee_team)
    assert user.teams.count() == 2


@pytest.mark.django_db
def test_auto_assign_group_membership_rules_second_login(env, client):
    central_it_team = env[0]
    employee_team = env[2]

    CasAttributeTeamAssignmentRule.objects.create(attribute="ou=central-it", team=central_it_team)

    login_mock(fake_cas_data, client)
    user = get_user(fake_cas_data)

    assert user.teams.count() == 1
    assert is_part_of_team(user, central_it_team)

    CasAttributeTeamAssignmentRule.objects.create(attribute="o=tu-darmstadt", team=employee_team)

    login_mock(fake_cas_data, client)
    user = get_user(fake_cas_data)

    assert is_part_of_team(user, central_it_team)
    assert is_part_of_team(user, employee_team)
    assert user.teams.count() == 2


@pytest.mark.django_db
def test_add_rules_in_settings(env, client):
    organizer = Organizer.objects.first()
    central_it = env[0]
    User.objects.create_superuser('admin@localhost', 'admin')
    admin = User.objects.get(email='admin@localhost')
    admin_team = Team.objects.create(organizer=organizer, can_change_organizer_settings=True)
    admin_team.members.add(admin)

    client.login(email='admin@localhost', password='admin')
    response = client.get(f'/control/organizer/{organizer.slug}/teams/assignment_rules')
    assert response.status_code == 200

    response = client.get(f'/control/organizer/{organizer.slug}/teams/assignment_rules/add')
    assert response.status_code == 200

    response = client.post(f'/control/organizer/{organizer.slug}/teams/assignment_rules/add', {
        'team': central_it.id,
        'attribute':  'ou=central-it'
    })
    assert response.status_code == 302

    assert CasAttributeTeamAssignmentRule.objects.count() == 1
    assert CasAttributeTeamAssignmentRule.objects.first().attribute == 'ou=central-it'
    assert CasAttributeTeamAssignmentRule.objects.first().team == central_it

    response = client.get(f'/control/organizer/{organizer.slug}/teams/assignment_rules/{42}/edit')
    assert response.status_code == 404

    response = client.post(f'/control/organizer/{organizer.slug}/teams/assignment_rules/{42}/delete')
    assert response.status_code == 404

    client.logout()


@pytest.mark.django_db
def test_add_ou_rule_in_settings(env, client):
    organizer = Organizer.objects.first()
    central_it = env[0]
    User.objects.create_superuser('admin@localhost', 'admin')
    admin = User.objects.get(email='admin@localhost')
    admin_team = Team.objects.create(organizer=organizer, can_change_organizer_settings=True)
    admin_team.members.add(admin)
    client.login(email='admin@localhost', password='admin')

    client.post(f'/control/organizer/{organizer.slug}/teams/assignment_rules/add', {
        'team': central_it.id,
        'attribute': 'FB20'
    })
    assert CasAttributeTeamAssignmentRule.objects.count() == 1
    assert CasAttributeTeamAssignmentRule.objects.first().attribute == 'FB20'
    assert CasAttributeTeamAssignmentRule.objects.first().team == central_it

    user = get_user(fake_cas_data)
    assert user.teams.count == 0

    login_mock(fake_cas_data, client)

    assert user.teams.count == 1
    assert is_part_of_team(user, central_it)


@pytest.mark.django_db
def test_add_ou_rule_in_settings(env, client):
    organizer = Organizer.objects.first()
    central_it = env[0]
    some_team = env[1]
    employee_team = env[2]
    User.objects.create_superuser('admin@localhost', 'admin')
    admin = User.objects.get(email='admin@localhost')
    admin_team = Team.objects.create(organizer=organizer, can_change_organizer_settings=True)
    admin_team.members.add(admin)
    client.login(email='admin@localhost', password='admin')

    client.post(f'/control/organizer/{organizer.slug}/teams/assignment_rules/add', {
        'team': employee_team.id,
        'attribute': 'o=tu-darmstadt'
    })
    client.post(f'/control/organizer/{organizer.slug}/teams/assignment_rules/add', {
        'team': central_it.id,
        'attribute': 'FB20'
    })
    client.post(f'/control/organizer/{organizer.slug}/teams/assignment_rules/add', {
        'team': some_team.id,
        'attribute': 'tu-darmstadt'  # This does not match
    })

    login_mock(fake_cas_data, client)
    user = get_user(fake_cas_data)
    assert user.teams.count() == 2
    assert is_part_of_team(user, central_it)
    assert is_part_of_team(user, employee_team)


@pytest.mark.django_db
def test_add_rules_in_settings_insufficient_permissions(env, client):
    organizer = Organizer.objects.first()

    User.objects.create_user('test@example.org', 'password')
    client.login(email='test@example.org', password='password')

    response = client.get(f'/control/organizer/{organizer.slug}/teams/assignment_rules')
    assert response.status_code == 404

    response = client.post(f'/control/organizer/{organizer.slug}/teams/assignment_rules/add')
    assert response.status_code == 404

    response = client.post(f'/control/organizer/{organizer.slug}/teams/assignment_rules/1/edit')
    assert response.status_code == 404

    response = client.get(f'/control/organizer/{organizer.slug}/teams/assignment_rules/1/edit')
    assert response.status_code == 404

    response = client.post(f'/control/organizer/{organizer.slug}/teams/assignment_rules/1/delete')
    assert response.status_code == 404

    client.logout()
