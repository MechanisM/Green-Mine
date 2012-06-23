# -* coding: utf-8 -*-

from django.conf import settings
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone
from django.core.files.storage import FileSystemStorage
from django.template.defaultfilters import slugify
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.contrib.auth.models import User
from django.contrib.auth.models import UserManager

from greenmine.core.fields import DictField, ListField, WikiField
from greenmine.core.utils import iter_points

import datetime
import re

ORG_ROLE_CHOICES = (
    ('owner', _(u'Owner')),
    ('developer', _(u'Developer')),
)

MARKUP_TYPE = (
    ('md', _(u'Markdown')),
    ('rst', _('Restructured Text')),
)

US_STATUS_CHOICES = (
    ('open', _(u'New')),
    ('progress', _(u'In progress')),
    ('completed', _(u'Ready for test')),
    ('closed', _(u'Closed')),
)

TASK_PRIORITY_CHOICES = (
    (1, _(u'Low')),
    (3, _(u'Normal')),
    (5, _(u'High')),
)


TASK_TYPE_CHOICES = (
    ('bug', _(u'Bug')),
    ('task', _(u'Task')),
)

TASK_STATUS_CHOICES = US_STATUS_CHOICES + (
    ('workaround', _(u"Workaround")),
    ('needinfo', _(u"Needs info")),
    ('posponed', _(u"Posponed")),
)

POINTS_CHOICES = (
    (-1, u'?'),
    (0, u'0'),
    (-2, u'1/2'),
    (1, u'1'),
    (2, u'2'),
    (3, u'3'),
    (5, u'5'),
    (8, u'8'),
    (10, u'10'),
    (15, u'15'),
    (20, u'20'),
    (40, u'40'),
)


TASK_COMMENT = 1
TASK_STATUS_CHANGE = 2
TASK_PRIORITY_CHANGE = 3
TASK_ASSIGNATION_CHANGE = 4

TASK_CHANGE_CHOICES = (
    (TASK_COMMENT, _(u"Task comment")),
    (TASK_STATUS_CHANGE, _(u"Task status change")),
    (TASK_PRIORITY_CHANGE, _(u"Task prioriy change")),
    (TASK_ASSIGNATION_CHANGE, _(u"Task assignation change")),
)


def slugify_uniquely(value, model, slugfield="slug"):
    """
    Returns a slug on a name which is unique within a model's table
    self.slug = SlugifyUniquely(self.name, self.__class__)
    """
    suffix = 0
    potential = base = slugify(value)
    if len(potential) == 0:
        potential = 'null'
    while True:
        if suffix:
            potential = "-".join([base, str(suffix)])
        if not model.objects.filter(**{slugfield: potential}).count():
            return potential
        suffix += 1


def ref_uniquely(project, model, field='ref'):
    """
    Returns a unique reference code based on base64 and time.
    """

    import time
    from django.utils import baseconv

    # this prevents concurrent and inconsistent references.
    time.sleep(0.1)

    new_timestamp = lambda: int("".join(str(time.time()).split(".")))
    while True:
        potential = baseconv.base62.encode(new_timestamp())
        params = {field: potential, 'project': project}
        if not model.objects.filter(**params).exists():
            return potential

        time.sleep(0.0002)


class Profile(models.Model):
    user = models.OneToOneField("auth.User", related_name='profile')
    description = WikiField(blank=True)
    photo = models.FileField(upload_to="files/msg",
        max_length=500, null=True, blank=True)

    default_language = models.CharField(max_length=20,
        null=True, blank=True, default=None)
    default_timezone = models.CharField(max_length=20,
        null=True, blank=True, default=None)
    token = models.CharField(max_length=200, unique=True,
        null=True, blank=True, default=None)


class Role(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=250, unique=True, blank=True)

    project_view = models.BooleanField(default=True)
    project_edit = models.BooleanField(default=False)
    project_delete = models.BooleanField(default=False)
    userstory_view = models.BooleanField(default=True)
    userstory_create = models.BooleanField(default=False)
    userstory_edit = models.BooleanField(default=False)
    userstory_delete = models.BooleanField(default=False)
    milestone_view = models.BooleanField(default=True)
    milestone_create = models.BooleanField(default=False)
    milestone_edit = models.BooleanField(default=False)
    milestone_delete = models.BooleanField(default=False)
    task_view = models.BooleanField(default=True)
    task_create = models.BooleanField(default=False)
    task_edit = models.BooleanField(default=False)
    task_delete = models.BooleanField(default=False)
    wiki_view = models.BooleanField(default=True)
    wiki_create = models.BooleanField(default=False)
    wiki_edit = models.BooleanField(default=False)
    wiki_delete = models.BooleanField(default=False)
    question_view = models.BooleanField(default=True)
    question_create = models.BooleanField(default=True)
    question_edit = models.BooleanField(default=True)
    question_delete = models.BooleanField(default=False)
    document_view = models.BooleanField(default=True)
    document_create = models.BooleanField(default=True)
    document_edit = models.BooleanField(default=True)
    document_delete = models.BooleanField(default=True)


class ProjectManager(models.Manager):
    def get_by_natural_key(self, slug):
        return self.get(slug=slug)

    def can_view(self, user):
        queryset = ProjectUserRole.objects.filter(user=user)\
            .values_list('project', flat=True)
        return Project.objects.filter(pk__in=queryset)


class ProjectExtras(models.Model):
    task_parser_re = models.CharField(max_length=1000, blank=True, null=True, default=None)
    sprints = models.IntegerField(default=1, blank=True, null=True)
    show_burndown = models.BooleanField(default=False, blank=True)
    show_burnup = models.BooleanField(default=False, blank=True)
    show_sprint_burndown = models.BooleanField(default=False, blank=True)
    total_story_points = models.FloatField(default=None, null=True)

    def get_task_parse_re(self):
        re_str = settings.DEFAULT_TASK_PARSER_RE
        if self.task_parser_re:
            re_str = self.task_parser_re
        return re.compile(re_str, flags=re.U+re.M)

    def parse_ustext(self, text):
        rx = self.get_task_parse_re()
        texts = rx.findall(text)
        for text in texts:
            yield text


class Project(models.Model):
    name = models.CharField(max_length=250, unique=True)
    slug = models.SlugField(max_length=250, unique=True, blank=True)
    description = WikiField(blank=False)

    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now_add=True)

    owner = models.ForeignKey("auth.User", related_name="projects")
    participants = models.ManyToManyField('auth.User',
        related_name="projects_participant", through="ProjectUserRole",
        null=True, blank=True)

    public = models.BooleanField(default=True)

    meta_category_list = ListField(null=True, default=[], editable=False)
    meta_category_color = DictField(null=True, default={}, editable=False)
    markup = models.CharField(max_length=10, choices=MARKUP_TYPE, default='md')

    extras = models.OneToOneField("ProjectExtras", related_name="project", null=True, default=None)

    objects = ProjectManager()

    def __unicode__(self):
        return self.name

    def get_extras(self):
        if self.extras is None:
            self.extras = ProjectExtras.objects.create()
            self.__class__.objects.filter(pk=self.pk).update(extras=self.extras)

        return self.extras

    def natural_key(self):
        return (self.slug,)

    @property
    def unasociated_user_stories(self):
        return self.user_stories.filter(milestone__isnull=True)

    @property
    def all_participants(self):
        qs = ProjectUserRole.objects.filter(project=self)
        return User.objects.filter(id__in=qs.values_list('user__pk', flat=True))

    @property
    def default_milestone(self):
        return self.milestones.order_by('-created_date')[0]

    def __repr__(self):
        return u"<Project %s>" % (self.slug)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify_uniquely(self.name, self.__class__)
        else:
            self.modified_date = timezone.now()

        super(Project, self).save(*args, **kwargs)

    def add_user(self, user, role):
        from greenmine import permissions
        return ProjectUserRole.objects.create(
            project = self,
            user = user,
            role = permissions.get_role(role),
        )


    """ Permalinks """

    @models.permalink
    def get_dashboard_url(self):
        return ('dashboard', (), {'pslug': self.slug})

    @models.permalink
    def get_backlog_url(self):
        return ('project-backlog', (),
            {'pslug': self.slug})

    @models.permalink
    def get_backlog_stats_url(self):
        return ('project-backlog-stats', (),
            {'pslug': self.slug})

    @models.permalink
    def get_backlog_left_block_url(self):
        return ('project-backlog-left-block', (),
            {'pslug': self.slug})

    @models.permalink
    def get_backlog_right_block_url(self):
        return ('project-backlog-right-block', (),
            {'pslug': self.slug})

    @models.permalink
    def get_backlog_burndown_url(self):
        return ('project-backlog-burndown', (),
            {'pslug': self.slug})

    @models.permalink
    def get_backlog_burnup_url(self):
        return ('project-backlog-burnup', (),
            {'pslug': self.slug})

    @models.permalink
    def get_milestone_create_url(self):
        return ('milestone-create', (),
            {'pslug': self.slug})

    @models.permalink
    def get_userstory_create_url(self):
        return ('user-story-create', (), {'pslug': self.slug})

    @models.permalink
    def get_edit_url(self):
        return ('project-edit', (), {'pslug': self.slug})

    @models.permalink
    def get_delete_url(self):
        return ('project-delete', (), {'pslug': self.slug})

    @models.permalink
    def get_export_url(self):
        return ('project-export-settings', (), {'pslug': self.slug})

    @models.permalink
    def get_export_now_url(self):
        return ('project-export-settings-now', (), {'pslug': self.slug})

    @models.permalink
    def get_export_rehash_url(self):
        return ('project-export-settings-rehash', (), {'pslug': self.slug})

    @models.permalink
    def get_default_tasks_url(self):
        return ('tasks-view', (),
            {'pslug': self.slug, 'mid': self.default_milestone.id })

    @models.permalink
    def get_tasks_url(self):
        return ('tasks-view', (), {'pslug': self.slug})

    @models.permalink
    def get_settings_url(self):
        return ('project-personal-settings', (), {'pslug': self.slug})

    @models.permalink
    def get_general_settings_url(self):
        return ('project-general-settings', (), {'pslug': self.slug})

    @models.permalink
    def get_questions_url(self):
        return ('questions', (), {'pslug': self.slug})

    @models.permalink
    def get_questions_create_url(self):
        return ('questions-create', (), {'pslug': self.slug})

    @models.permalink
    def get_documents_url(self):
        return ('documents', (), {'pslug': self.slug})


class Team(models.Model):
    name = models.CharField(max_length=200)
    project = models.ForeignKey('Project', related_name='teams')
    users = models.ManyToManyField('auth.User',
        related_name='teams', null=True, default=None)

    class Meta:
        unique_together = ('name', 'project')


class ProjectUserRole(models.Model):
    project = models.ForeignKey("Project", related_name="user_roles")
    user = models.ForeignKey("auth.User", related_name="user_roles")
    role = models.ForeignKey("Role", related_name="user_roles")

    mail_milestone_created = models.BooleanField(default=True)
    mail_milestone_modified = models.BooleanField(default=False)
    mail_milestone_deleted = models.BooleanField(default=False)
    mail_userstory_created = models.BooleanField(default=True)
    mail_userstory_modified = models.BooleanField(default=False)
    mail_userstory_deleted = models.BooleanField(default=False)
    mail_task_created = models.BooleanField(default=True)
    mail_task_assigned = models.BooleanField(default=False)
    mail_task_deleted = models.BooleanField(default=False)
    mail_question_created = models.BooleanField(default=False)
    mail_question_assigned = models.BooleanField(default=True)
    mail_question_deleted = models.BooleanField(default=False)
    mail_document_created = models.BooleanField(default=True)
    mail_document_deleted = models.BooleanField(default=False)
    mail_wiki_created = models.BooleanField(default=False)
    mail_wiki_modified = models.BooleanField(default=False)
    mail_wiki_deleted = models.BooleanField(default=False)

    def __repr__(self):
        return u"<Project-User-Relation-%s>" % (self.id)

    class Meta:
        unique_together = ('project', 'user')


class MilestoneManager(models.Manager):
    def get_by_natural_key(self, name, project):
        return self.get(name=name, project__slug=project)


class Milestone(models.Model):
    name = models.CharField(max_length=200, db_index=True)
    owner = models.ForeignKey('auth.User', related_name="milestones")
    project = models.ForeignKey('Project', related_name="milestones")

    estimated_start = models.DateField(null=True, default=None)
    estimated_finish = models.DateField(null=True, default=None)

    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now_add=True)
    closed = models.BooleanField(default=False)

    disponibility = models.FloatField(null=True, default=0.0)
    objects = MilestoneManager()

    class Meta:
        ordering = ['-created_date']
        unique_together = ('name', 'project')

    @property
    def total_points(self):
        """
        Get total story points for this milestone.
        """

        total = sum(iter_points(self.user_stories.all()))
        return "{0:.1f}".format(total)

    def get_points_done_at_date(self, date):
        """
        Get completed story points for this milestone before the date.
        """
        total = 0.0

        for item in self.user_stories.filter(status__in=settings.CLOSED_STATUSES):
            if item.tasks.filter(modified_date__lt=date).count() > 0:
                if item.points == -1:
                    continue

                if item.points == -2:
                    total += 0.5
                    continue

                total += item.points

        return "{0:.1f}".format(total)

    @property
    def completed_points(self):
        """
        Get a total of completed points.
        """

        queryset = self.user_stories.filter(status__in=settings.CLOSED_STATUSES)
        total = sum(iter_points(queryset))
        return "{0:.1f}".format(total)

    @property
    def percentage_completed(self):
        return "{0:.1f}".format(
            (float(self.completed_points) * 100) / float(self.total_points)
        )

    @models.permalink
    def get_edit_url(self):
        return ('milestone-edit', (),
            {'pslug': self.project.slug, 'mid': self.id})

    @models.permalink
    def get_delete_url(self):
        return ('milestone-delete', (),
            {'pslug': self.project.slug, 'mid': self.id})

    @models.permalink
    def get_dashboard_url(self):
        return ('dashboard', (),
            {'pslug': self.project.slug, 'mid': self.id})

    @models.permalink
    def get_burndown_url(self):
        return ('milestone-burndown', (),
            {'pslug': self.project.slug, 'mid': self.id})

    @models.permalink
    def get_user_story_create_url(self):
        return ('user-story-create', (),
            {'pslug': self.project.slug, 'mid': self.id})

    @models.permalink
    def get_ml_detail_url(self):
        return ('milestone-dashboard', (),
            {'pslug': self.project.slug, 'mid': self.id})

    @models.permalink
    def get_create_task_url(self):
        return ('api:task-create', (),
            {'pslug': self.project.slug, 'mid': self.id})

    @models.permalink
    def get_stats_api_url(self):
        return ('api:stats-milestone', (),
            {'pslug': self.project.slug, 'mid': self.id})

    @models.permalink
    def get_tasks_url(self):
        return ('tasks-view', (),
            {'pslug': self.project.slug, 'mid': self.id})

    @models.permalink
    def get_tasks_url_filter_by_task(self):
        return ('tasks-view', (),
            {'pslug': self.project.slug, 'mid': self.id, 'filter_by':'task'})

    @models.permalink
    def get_tasks_url_filter_by_bug(self):
        return ('tasks-view', (),
            {'pslug': self.project.slug, 'mid': self.id, 'filter_by':'bug'})

    @models.permalink
    def get_task_create_url(self):
        return ('task-create', (),
            {'pslug': self.project.slug, 'mid': self.id})

    class Meta(object):
        unique_together = ('name', 'project')

    def natural_key(self):
        return (self.name,) + self.project.natural_key()

    natural_key.dependencies = ['greenmine.Project']

    def __unicode__(self):
        return self.name

    def __repr__(self):
        return u"<Milestone %s>" % (self.id)

    def save(self, *args, **kwargs):
        if self.id:
            self.modified_date = timezone.now()

        super(Milestone, self).save(*args, **kwargs)


class UserStory(models.Model):
    ref = models.CharField(max_length=200, unique=True,
        db_index=True, null=True, default=None)
    milestone = models.ForeignKey("Milestone", blank=True,
        related_name="user_stories", null=True, default=None)
    project = models.ForeignKey("Project", related_name="user_stories")
    owner = models.ForeignKey("auth.User", null=True,
        default=None, related_name="user_stories")
    priority = models.IntegerField(default=1)
    points = models.IntegerField(choices=POINTS_CHOICES, default=-1)
    status = models.CharField(max_length=50,
        choices=US_STATUS_CHOICES, db_index=True, default="open")

    category = models.CharField(max_length=200, null=True, blank=True)

    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now_add=True)
    tested = models.BooleanField(default=False)

    subject = models.CharField(max_length=500)
    description = WikiField()
    finish_date = models.DateTimeField(null=True, blank=True)

    watchers = models.ManyToManyField('auth.User',
        related_name='us_watch', null=True)

    client_requirement = models.BooleanField(default=False)
    team_requirement = models.BooleanField(default=False)

    class Meta:
        unique_together = ('ref', 'project')

    def __repr__(self):
        return u"<UserStory %s>" % (self.id)

    def __unicode__(self):
        return u"{0} ({1})".format(self.subject, self.ref)

    def save(self, *args, **kwargs):
        if self.id:
            self.modified_date = timezone.now()
        if not self.ref:
            self.ref = ref_uniquely(self.project, self.__class__)

        super(UserStory, self).save(*args, **kwargs)

    @models.permalink
    def get_assign_url(self):
        return ('assign-us', (),
            {'pslug': self.project.slug, 'iref': self.ref})

    @models.permalink
    def get_unassign_url(self):
        return ('unassign-us', (),
            {'pslug': self.project.slug, 'iref': self.ref})

    @models.permalink
    def get_drop_api_url(self):
        # TODO: check if this url is used.
        return ('api:user-story-drop', (),
            {'pslug': self.project.slug, 'iref': self.ref})

    @models.permalink
    def get_view_url(self):
        return ('user-story', (),
            {'pslug': self.project.slug, 'iref': self.ref})

    @models.permalink
    def get_edit_url(self):
        return ('user-story-edit', (),
            {'pslug': self.project.slug, 'iref': self.ref})

    @models.permalink
    def get_edit_inline_url(self):
        return ('user-story-edit-inline', (),
            {'pslug': self.project.slug, 'iref': self.ref})

    @models.permalink
    def get_delete_url(self):
        return ('user-story-delete', (),
            {'pslug': self.project.slug, 'iref': self.ref})

    @models.permalink
    def get_task_create_url(self):
        return ('task-create', (),
            {'pslug': self.project.slug, 'usref': self.ref})

    """ Propertys """

    @property
    def tasks_new(self):
        return self.tasks.filter(status='open')

    @property
    def tasks_progress(self):
        return self.tasks.filter(status='progress')

    @property
    def tasks_completed(self):
        return self.tasks.filter(status='completed')

    @property
    def tasks_closed(self):
        return self.tasks.filter(status__in=['workaround', 'needinfo','closed', 'posponed'])

    def update_status(self):
        total_tasks_count = self.tasks.count()

        if total_tasks_count == 0:
            self.status = 'open'
        elif self.tasks.filter(status__in=settings.CLOSED_STATUSES).count() == total_tasks_count:
            self.status = 'completed'
        elif self.tasks.filter(status='open').count() == total_tasks_count:
            self.status = 'open'
        else:
            self.status = 'progress'

        self.modified_date = timezone.now()
        self.save()


class Change(models.Model):
    change_type = models.IntegerField(choices=TASK_CHANGE_CHOICES)
    owner = models.ForeignKey('auth.User', related_name='changes')
    created_date = models.DateTimeField(auto_now_add=True)

    project = models.ForeignKey("Project", related_name="changes")

    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = generic.GenericForeignKey('content_type', 'object_id')

    data = DictField()


class ChangeAttachment(models.Model):
    change = models.ForeignKey("Change", related_name="attachments")
    owner = models.ForeignKey("auth.User", related_name="change_attachments")

    created_date = models.DateTimeField(auto_now_add=True)
    attached_file = models.FileField(upload_to="files/msg",
        max_length=500, null=True, blank=True)


class Task(models.Model):
    user_story = models.ForeignKey('UserStory', related_name='tasks', null=True, blank=True)
    ref = models.CharField(max_length=200, unique=True,
        db_index=True, null=True, default=None)
    status = models.CharField(max_length=50,
        choices=TASK_STATUS_CHOICES, default='open')
    owner = models.ForeignKey("auth.User", null=True,
        default=None, related_name="tasks")

    priority = models.IntegerField(choices=TASK_PRIORITY_CHOICES, default=3)
    milestone = models.ForeignKey('Milestone', related_name='tasks',
        null=True, default=None, blank=True)

    project = models.ForeignKey('Project', related_name='tasks')
    type = models.CharField(max_length=10,
        choices=TASK_TYPE_CHOICES, default='task')

    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now_add=True)

    subject = models.CharField(max_length=500)
    description = WikiField(blank=True)
    assigned_to = models.ForeignKey('auth.User',
        related_name='user_storys_assigned_to_me',
        blank=True, null=True, default=None)

    watchers = models.ManyToManyField('auth.User',
        related_name='task_watch', null=True)

    changes = generic.GenericRelation(Change)

    class Meta:
        unique_together = ('ref', 'project')

    @property
    def has_noncolumn_status(self):
        return self.status in ['needinfo', 'workaround', 'posponed']

    @models.permalink
    def get_edit_url(self):
        return ('task-edit', (), {
            'pslug': self.project.slug,
            'tref': self.ref
        })

    @models.permalink
    def get_alter_api_url(self):
        return ('api:task-alter', (), {
            'pslug': self.project.slug,
            'taskref': self.ref
        })

    @models.permalink
    def get_reassign_api_url(self):
        return ('api:task-reassing', (), {
            'pslug': self.project.slug,
            'taskref': self.ref
        })

    @models.permalink
    def get_view_url(self):
        return ('task-view', (),
            {'pslug':self.project.slug, 'tref': self.ref})

    @models.permalink
    def get_delete_url(self):
        return ('task-delete', (),
            {'pslug':self.project.slug, 'tref': self.ref})

    def save(self, *args, **kwargs):
        if self.id:
            self.modified_date = timezone.now()

        if not self.ref:
            self.ref = ref_uniquely(self.project, self.__class__)

        super(Task, self).save(*args, **kwargs)



class TemporalFile(models.Model):
    attached_file = models.FileField(upload_to="temporal_files",
        max_length=1000, null=True, blank=True)

    owner = models.ForeignKey('auth.User', related_name='tmpfiles')
    created_date = models.DateTimeField(auto_now_add=True)


class Document(models.Model):
    title = models.CharField(max_length=150)
    slug = models.SlugField(unique=True, max_length=200, blank=True)
    description = WikiField(blank=True)

    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now_add=True)

    project = models.ForeignKey('Project', related_name='documents')
    owner = models.ForeignKey('auth.User', related_name='documents')
    attached_file = models.FileField(upload_to="documents",
        max_length=1000, null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify_uniquely(self.title, self.__class__)
        super(Document, self).save(*args, **kwargs)

    @models.permalink
    def get_delete_url(self):
        return ('documents-delete', (),
            {'pslug': self.project.slug, 'docid': self.pk})


class Question(models.Model):
    subject = models.CharField(max_length=150)
    slug = models.SlugField(unique=True, max_length=250, blank=True)
    content = WikiField(blank=True)
    closed = models.BooleanField(default=False)
    attached_file = models.FileField(upload_to="messages",
        max_length=500, null=True, blank=True)

    project = models.ForeignKey('Project', related_name='questions')
    milestone = models.ForeignKey('Milestone', related_name='questions',
        null=True, default=None, blank=True)

    assigned_to = models.ForeignKey("auth.User")
    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now_add=True)
    owner = models.ForeignKey('auth.User', related_name='questions')


    watchers = models.ManyToManyField('auth.User',
        related_name='question_watch', null=True, blank=True)

    @models.permalink
    def get_view_url(self):
        return ('questions-view', (),
            {'pslug': self.project.slug, 'qslug': self.slug})

    @models.permalink
    def get_edit_url(self):
        return ('questions-edit', (),
            {'pslug': self.project.slug, 'qslug': self.slug})

    @models.permalink
    def get_delete_url(self):
        return ('questions-delete', (),
            {'pslug': self.project.slug, 'qslug': self.slug})

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify_uniquely(self.subject, self.__class__)
        super(Question, self).save(*args, **kwargs)


class QuestionResponse(models.Model):
    content = WikiField()
    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now_add=True)
    attached_file = models.FileField(upload_to="messages",
        max_length=500, null=True, blank=True)

    question = models.ForeignKey('Question', related_name='responses')
    owner = models.ForeignKey('auth.User', related_name='questions_responses')


class WikiPage(models.Model):
    project = models.ForeignKey('Project', related_name='wiki_pages')
    slug = models.SlugField(max_length=500, db_index=True)
    content = WikiField(blank=False, null=True)
    owner = models.ForeignKey("auth.User", related_name="wiki_pages", null=True)

    watchers = models.ManyToManyField('auth.User',
        related_name='wikipage_watchers', null=True)

    created_date = models.DateTimeField(auto_now_add=True)

    @models.permalink
    def get_view_url(self):
        return ('wiki-page', (),
            {'pslug': self.project.slug, 'wslug': self.slug})

    @models.permalink
    def get_edit_url(self):
        return ('wiki-page-edit', (),
            {'pslug': self.project.slug, 'wslug': self.slug})

    @models.permalink
    def get_delete_url(self):
        return ('wiki-page-delete', (),
            {'pslug': self.project.slug, 'wslug': self.slug})

    @models.permalink
    def get_history_view_url(self):
        return ('wiki-page-history', (),
            {'pslug': self.project.slug, 'wslug': self.slug})



class WikiPageHistory(models.Model):
    wikipage = models.ForeignKey("WikiPage", related_name="history_entries")
    content = WikiField(blank=True, null=True)
    created_date = models.DateTimeField()
    owner = models.ForeignKey("auth.User", related_name="wiki_page_historys")

    # TODO: fix this permalink. this implementation is bad for performance.

    @models.permalink
    def get_history_view_url(self):
        return ('wiki-page-history-view', (),
            {'pslug': self.wikipage.project.slug, 'wslug': self.wikipage.slug, 'hpk': self.pk})


class WikiPageAttachment(models.Model):
    wikipage = models.ForeignKey('WikiPage', related_name='attachments')
    owner = models.ForeignKey("auth.User", related_name="wikifiles")
    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now_add=True)
    attached_file = models.FileField(upload_to="files/wiki",
        max_length=500, null=True, blank=True)


class ExportDirectoryCache(models.Model):
    path = models.CharField(max_length=500)
    size = models.IntegerField(null=True)


# load signals
from . import sigdispatch
