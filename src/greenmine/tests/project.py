# -*- coding: utf-8 -*-

from django.test import TestCase
from django.core import mail
from django.core.urlresolvers import reverse
from django.utils import simplejson as json

from django.contrib.auth.models import User
from ..models import *

from greenmine import permissions as perms

class ProjectRelatedTests(TestCase):
    def setUp(self):
        self.user = User.objects.create(
            username = 'test',
            email = 'test@test.com',
            is_active = True,
            is_staff = False,
            is_superuser = False,
        )
        self.user.set_password('test')
        self.user.save()
        self.client.login(username='test', password='test')

    def tearDown(self):
        ProjectUserRole.objects.all().delete()
        Project.objects.all().delete()
        User.objects.all().delete()
        self.client.logout()

    def test_home_projects_view(self):
        home_url = reverse('web:projects')
        response = self.client.get(home_url)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['projects'].count(), 0)

        self.assertIn("page", response.context)
        self.assertIn("is_paginated", response.context)

    def test_create_project(self):
        post_params = {
            'name': 'test-project',
            'description': 'description',
            'user_{0}'.format(self.user.id): '1',
        }

        project_create_url = reverse('web:project-create')
        response = self.client.post(project_create_url, post_params, follow=True)

        self.assertEqual(response.status_code, 200)
        jdata = json.loads(response.content)
        self.assertTrue(jdata['valid'])

    def test_create_duplicate_project(self):
        self.test_create_project()

        post_params = {
            'name': 'test-project',
            'description': 'description',
            'user_{0}'.format(self.user.id): '1',
        }

        project_create_url = reverse('web:project-create')
        response = self.client.post(project_create_url, post_params, follow=True)

        self.assertEqual(response.status_code, 200)
        jdata = json.loads(response.content)
        self.assertFalse(jdata['valid'])

    def test_normal_user_projects(self):
        """
        Permission tests, normal user only show 
        owned projects and participant.
        """

        user1 = User.objects.create(
            username = 'test2',
            email = 'test2@test.com',
            is_active = True,
            is_staff = True,
            is_superuser = True,
            password = self.user.password,
        )

        Project.objects.bulk_create([
            Project(name='test1', description='test1', owner=self.user, slug='test1'),
            Project(name='test2', description='test2', owner=self.user, slug='test2'),
            Project(name='test3', description='test3', owner=user1, slug='test3'),
        ])

        home_url = reverse('web:projects')
        response = self.client.get(home_url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['projects'].count(), 2)

    def test_project_edit(self):
        project = Project(name='test1', description='test1', owner=self.user, slug='test1')
        project.save()

        pur = ProjectUserRole.objects.create(
            user = self.user,
            project = project,
            role = Role.objects.get(pk=1),
        )

        post_params = {
            'name': 'test-project2',
            'description': project.description,
            'user_{0}'.format(self.user.id): '2',
        }

        project_edit_url = reverse('web:project-edit', args=[project.slug])
        response = self.client.post(project_edit_url, post_params)
        self.assertEqual(response.status_code, 200)

        jdata = json.loads(response.content)
        self.assertTrue(jdata['valid'])
        self.assertIn("redirect_to", jdata)

        qs = ProjectUserRole.objects.filter(
            user = self.user,
            project = project,
            role__pk = 2,
        )
        self.assertEqual(qs.count(), 1)

    def test_get_project_edit_page_without_permision(self):
        """
        Test make GET request on a project edit form with
        some user with developer role, but without ownership of project.
        FIXME: this is unfinished test. Project edit/create form need big refactor.
        """

        user1 = User.objects.create(
            username = 'test2',
            email = 'test2@test.com',
            is_active = True,
            is_staff = True,
            is_superuser = True,
            password = self.user.password,
        )

        project = Project(name='test1', description='test1', owner=user1, slug='test1')
        project.save()
        
        pur = ProjectUserRole.objects.create(
            project = project,
            user = self.user,
            role = perms.get_role('developer'),
        )
        
        response = self.client.get(reverse('web:project-edit', args=[project.id]), follow=True)
        #print response.redirect_chain
        #self.assertEqual(response.redirect_chain, [('http://testserver/profile/', 302)])


class SimplePermissionMethodsTest(TestCase):
    def test_has_permission(self):
        user = User.objects.create(
            username = 'test',
            email = 'test@test.com',
            is_active = True,
            is_staff = False,
            is_superuser = False,
        )

        project = Project.objects.create(name='test1', description='test1', owner=user, slug='test1')
        role = perms.get_role('developer')

        pur = ProjectUserRole.objects.create(
            project = project,
            user = user,
            role = role,
        )

        self.assertTrue(perms.has_perm(user, project, "project", "view"))
        self.assertTrue(perms.has_perm(user, project, "task", "edit"))

        project.delete()
        user.delete()
        pur.delete()

    def test_has_multiple_permissions(self):
        user = User.objects.create(
            username = 'test',
            email = 'test@test.com',
            is_active = True,
            is_staff = False,
            is_superuser = False,
        )

        project = Project.objects.create(name='test1', description='test1', owner=user, slug='test1')
        role = perms.get_role('developer')

        pur = ProjectUserRole.objects.create(
            project = project,
            user = user,
            role = role,
        )
        
        self.assertTrue(perms.has_perms(user, project, [
            ('project', 'view'),
            ('milestone', 'view'),
            ('userstory', 'view'),
        ]))
    
    def tearDown(self):
        ProjectUserRole.objects.all().delete()
        Project.objects.all().delete()
        User.objects.all().delete()
