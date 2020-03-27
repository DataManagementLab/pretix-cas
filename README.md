# Pretix CAS SSO Plugin

![CI](https://github.com/DataManagementLab/pretix-cas/workflows/CI/badge.svg)

This is a plugin for [pretix] that provides a [pluggable authentication backend] for [Apereo CAS] SSO servers.

It also allows you to create rules that automatically assign users to teams based upon the attributes provided by the SSO Server.

## Table of contents
* [Usage](#usage)
    + [Login](#login)
    + [Team assignment rules](#team-assignment-rules)
* [Supported types of team assignment rules](#supported-types-of-team-assignment-rules)
* [General remarks](#general-remarks)
* [Installation](#installation)
* [Development setup](#development-setup)
* [License](#license)

## Usage

### Login

To log into pretix using the CAS authentication backend, click the button with the label "TU Darmstadt HRZ SSO".
Logging into pretix using the native authentication backend works just like without the plugin.
The only difference is that since there are two active authentication backends, the selection of the backend is available.

<img src="doc/login form.png" alt="Login form with native authentication backend and TU Darmstadt SSO Backend">

### Team assignment rules

To create a new team assignment rule, you need to activate the organizer account that the team is associated to.
This is done by selecting the corresponding organizer account in the dropdown menu:

<img src="doc/organizer dropdown.png" alt="organizer account selection dropdown menu">


Make sure that you have already [created the team] that you want to assign users to and that your account has the
"Can change organizer settings" permission.
To create a team assignment rule, go to the "Team assignment rules" section in the panel on the left and press the
"Create team assignment rule" button.

<img src="doc/empty team assignment rules with arrows.png" alt="sidepanel with arrow to team assignment rules column and arrow to create team assignment rule button ">


Next **select the team** that the users with the attributes are assigned to and **insert the attribute** to the text box.
Press **"Save"** to create the rule.

<img src="doc/modify or create team assignment rule.png" alt="creation of team assignment rule">


The rule should now be visible in the overview and can be modified or deleted by using the buttons on the right.


<img src="doc/team assignment rule created.png" alt="successful creation of team assignment rule with buttons for modification and deletion">

## Supported types of team assignment rules

Assignment rule attributes are checked against the **groupMembership** and **ou** CAS attributes of users.
When a user with the groupMembership attributes {..., o=tu-darmstadt, ...} logs in and there is an assignment rule with the attribute field "o=tu-darmstadt", the user is added to the corresponding team.
Assignment rules for ou attributes work similarly: A user with the ou attributes {..., FB20, ...} will be added to every team with an assignment rule with "FB20" in the attribute field.
The process of adding assignment rules with ou-attributes and groupMembership-attributes is the same.

To check your own attributes go to: [https://sso.tu-darmstadt.de/login?service=http://localhost](https://sso.tu-darmstadt.de/login?service=http://localhost)

## General remarks

- Since the attributes of the users are only accessible on login, they are only assigned to teams on every login through SSO.
- Users are not removed from teams when the associated assignment rule is removed

## Installation

1. Make sure that you have a working pretix installation. Please refer to: [official installation guide]
2. Make sure that you have activated your [python virtual environment] of your pretix installation
3. Install the plugin through `pip install pretix-cas`
4. Add the following to the [pretix configuration file] to activate the authentication backend:
   ```ini
   [pretix]
   ; Activate both the CAS authentication backend and the Native authentication backend
   auth_backends=pretix.base.auth.NativeAuthBackend,pretix_cas.auth_backend.CasAuthBackend
   ```
5. This plugin uses the TU Darmstadt CAS server by default. The default configuration can be overriden by adding a
   `[pretix_cas]` section to the [pretix configuration file]. The configuration for the example.org CAS server looks
   like this:
   ```ini
   [pretix_cas]
   ; CAS server URL
   cas_server_url=https://sso.example.org
   ; Name of the CAS authentication option that is displayed above the login prompt
   cas_server_name=Example Inc. SSO
   ; Default CAS version
   cas_version=CAS_2_SAML_1_0
   ```
6. Restart the pretix server. You should now be able to login through CAS and manage team assignment rules.

## Development setup

1. Make sure that you have a working [pretix development setup].
2. Clone this repository, e.g. to ``local/pretix-cas``.
3. Activate the virtual environment you use for pretix development.
4. Execute ``python setup.py develop`` within this directory to register this application with pretix's plugin registry.
5. Execute ``make`` within this directory to compile translations.
6. Create a [pretix configuration file] with at least the following in it:
   ```ini
   [pretix]
   auth_backends=pretix.base.auth.NativeAuthBackend,pretix_cas.auth_backend.CasAuthBackend
   ```
7. Restart your local pretix server. You can now use the plugin from this repository.
   
## License

Copyright 2019 - 2020, Benjamin Hättasch and TU Darmstadt Bachelorpraktikum 2019/2020 Group 45

Released under the terms of the Apache License 2.0

[pretix]: https://github.com/pretix/pretix
[Apereo CAS]: https://www.apereo.org/projects/cas
[pretix development setup]: https://docs.pretix.eu/en/latest/development/setup.html
[pretix configuration file]: https://docs.pretix.eu/en/latest/admin/config.html
[pluggable authentication backend]: https://docs.pretix.eu/en/latest/development/api/auth.html
[created the team]: https://docs.pretix.eu/en/latest/user/organizers/teams.html
[official installation guide]: https://docs.pretix.eu/en/latest/admin/installation/index.html
[python virtual environment]: https://docs.python.org/3/library/venv.html
