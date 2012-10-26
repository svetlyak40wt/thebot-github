from __future__ import absolute_import, unicode_literals

import anyjson
import requests
import threading
import time

from thebot import Plugin, on_command


class Plugin(Plugin):
    def __init__(self, args):
        super(Plugin, self).__init__(args)
        self._issues = {}
        self._issues_map = {}
        self._track_request = self.storage.get('track_request')

    @staticmethod
    def get_options(parser):
        group = parser.add_argument_group('GitHub options')
        group.add_argument(
            '--github-api', default='https://api.github.com',
            help='Base URL to GitHub\'s api. Default: https://api.github.com.'
        )

    @on_command('/github')
    def web_hook(self, request):
        event = request.environ['HTTP_X_GITHUB_EVENT']
        payload = anyjson.deserialize(request.POST['payload'][0])

        if self._track_request is not None:
            self._track_request.respond('Received {} hook'.format(event))

        callback = getattr(self, 'on_' + event.lower(), None)
        if callback is not None:
            callback(request, payload)

    @on_command('gh track')
    def track(self, request):
        self.storage['track_request'] = request
        request.respond('I\'ll track github requests now')

    @on_command('track issues (?P<username>.+)/(?P<repository>.+)')
    def track_issues(self, request, username, repository):
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


    @on_command('show issues (?P<username>.+)/(?P<repository>.+)')
    def show_issues(self, request, username, repository):
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

