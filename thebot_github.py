from __future__ import absolute_import

import anyjson
import requests
import thebot
import threading
import time


class Plugin(thebot.Plugin):
    def __init__(self, args):
        super(Plugin, self).__init__(args)
        self._issues = {}
        self._issues_map = {}

    @staticmethod
    def get_options(parser):
        group = parser.add_argument_group('GitHub options')
        group.add_argument(
            '--github-api', default='https://api.github.com',
            help='Base URL to GitHub\'s api. Default: https://api.github.com.'
        )

    def get_callbacks(self):
        return [
            ('show issues (?P<username>.+)/(?P<repository>.+)', self.show_issues),
            ('track issues (?P<username>.+)/(?P<repository>.+)', self.track_issues),
            ('print multiline', self.print_lines),
        ]

    def print_lines(self, request, match):
        request.respond('Some line\nwith a newline.')

    def track_issues(self, request, match):
        username, repository = match.group('username'), match.group('repository')

        issues = self.get_issues(request, username, repository)
        if issues is not None:
            issues_numbers = set(item['number'] for item in issues)
            issues_map = dict((item['number'], item) for item in issues)

            key = username + '/' + repository
            self._issues[key] = issues_numbers
            self._issues_map[key] = issues_map

            def track():
                while True:
                    time.sleep(15)
                    issues = self.get_issues(request, username, repository)
                    new_issues = set(item['number'] for item in issues)
                    new_issues_map = dict((item['number'], item) for item in issues)

                    old_issues = self._issues[key]
                    old_issues_map = self._issues_map[key]

                    if old_issues != new_issues:
                        opened = new_issues - old_issues
                        closed = old_issues - new_issues

                        if opened:
                            request.respond(
                                'These issues were opened in {}/{}:\n'.format(username, repository) +
                                '\n'.join(
                                    '{number}) {title}'.format(**item)
                                    for item in issues
                                        if item['number'] in opened
                                )
                            )

                        if closed:
                            request.respond(
                                'These issues were closed in {}/{}:\n'.format(username, repository) +
                                '\n'.join(
                                    '{number}) {title}'.format(**item)
                                    for item in old_issues_map.values()
                                        if item['number'] in closed
                                )
                            )
                        self._issues[key] = new_issues
                        self._issues_map[key] = new_issues_map

            thread = threading.Thread(target=track)
            thread.daemon = True
            thread.start()


    def show_issues(self, request, match):
        username, repository = match.group('username'), match.group('repository')
        data = self.get_issues(request, username, repository)

        if data is not None:
            request.respond('\n'.join(
                '{number}) {title}'.format(**item)
                for item in data
            ))

    def get_issues(self, request, username, repository):
        response = requests.get(
            '{}/repos/{}/{}/issues'.format(
                self.args.github_api,
                username,
                repository
            )
        )
        if response.status_code == 200:
            return anyjson.deserialize(response.content)
        elif response.status_code == 404:
            request.respond('Repository {}/{} not found.'.format(username, repository))
        else:
            request.respond('I\'ve received {} HTTP error from the GitHub.'.format(response.status_code))
