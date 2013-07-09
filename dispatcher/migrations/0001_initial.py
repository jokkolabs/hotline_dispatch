# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'HotlineEvent'
        db.create_table(u'dispatcher_hotlineevent', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('identity', self.gf('django.db.models.fields.CharField')(max_length=30)),
            ('event_type', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('received_on', self.gf('django.db.models.fields.DateTimeField')()),
            ('created_on', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('hotline_number', self.gf('django.db.models.fields.CharField')(max_length=30, null=True, blank=True)),
            ('sms_message', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('processed', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('operator', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('volunteer', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['dispatcher.HotlineVolunteer'], null=True, blank=True)),
            ('archived', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal(u'dispatcher', ['HotlineEvent'])

        # Adding unique constraint on 'HotlineEvent', fields ['identity', 'received_on']
        db.create_unique(u'dispatcher_hotlineevent', ['identity', 'received_on'])

        # Adding model 'HotlineVolunteer'
        db.create_table(u'dispatcher_hotlinevolunteer', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('password', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('last_login', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('is_superuser', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('username', self.gf('django.db.models.fields.CharField')(unique=True, max_length=30)),
            ('first_name', self.gf('django.db.models.fields.CharField')(max_length=30, blank=True)),
            ('last_name', self.gf('django.db.models.fields.CharField')(max_length=30, blank=True)),
            ('email', self.gf('django.db.models.fields.EmailField')(max_length=75, blank=True)),
            ('is_staff', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('is_active', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('date_joined', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('operator', self.gf('django.db.models.fields.CharField')(max_length=50, null=True, blank=True)),
            ('phone_number', self.gf('django.db.models.fields.CharField')(max_length=30, null=True, blank=True)),
        ))
        db.send_create_signal(u'dispatcher', ['HotlineVolunteer'])

        # Adding M2M table for field groups on 'HotlineVolunteer'
        m2m_table_name = db.shorten_name(u'dispatcher_hotlinevolunteer_groups')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('hotlinevolunteer', models.ForeignKey(orm[u'dispatcher.hotlinevolunteer'], null=False)),
            ('group', models.ForeignKey(orm[u'auth.group'], null=False))
        ))
        db.create_unique(m2m_table_name, ['hotlinevolunteer_id', 'group_id'])

        # Adding M2M table for field user_permissions on 'HotlineVolunteer'
        m2m_table_name = db.shorten_name(u'dispatcher_hotlinevolunteer_user_permissions')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('hotlinevolunteer', models.ForeignKey(orm[u'dispatcher.hotlinevolunteer'], null=False)),
            ('permission', models.ForeignKey(orm[u'auth.permission'], null=False))
        ))
        db.create_unique(m2m_table_name, ['hotlinevolunteer_id', 'permission_id'])

        # Adding model 'HotlineResponse'
        db.create_table(u'dispatcher_hotlineresponse', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('request', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['dispatcher.HotlineEvent'], unique=True)),
            ('created_on', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('response_date', self.gf('django.db.models.fields.DateTimeField')()),
            ('age', self.gf('django.db.models.fields.PositiveIntegerField')(null=True, blank=True)),
            ('sex', self.gf('django.db.models.fields.CharField')(default=u'U', max_length=u'1')),
            ('duration', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('location', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['dispatcher.Entity'], null=True, blank=True)),
        ))
        db.send_create_signal(u'dispatcher', ['HotlineResponse'])

        # Adding M2M table for field topics on 'HotlineResponse'
        m2m_table_name = db.shorten_name(u'dispatcher_hotlineresponse_topics')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('hotlineresponse', models.ForeignKey(orm[u'dispatcher.hotlineresponse'], null=False)),
            ('topics', models.ForeignKey(orm[u'dispatcher.topics'], null=False))
        ))
        db.create_unique(m2m_table_name, ['hotlineresponse_id', 'topics_id'])

        # Adding model 'Entity'
        db.create_table(u'dispatcher_entity', (
            ('slug', self.gf('django.db.models.fields.CharField')(max_length=20, primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('type', self.gf('django.db.models.fields.CharField')(max_length=30)),
            ('latitude', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('longitude', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('parent', self.gf('mptt.fields.TreeForeignKey')(blank=True, related_name=u'children', null=True, to=orm['dispatcher.Entity'])),
            ('lft', self.gf('django.db.models.fields.PositiveIntegerField')(db_index=True)),
            ('rght', self.gf('django.db.models.fields.PositiveIntegerField')(db_index=True)),
            ('tree_id', self.gf('django.db.models.fields.PositiveIntegerField')(db_index=True)),
            ('level', self.gf('django.db.models.fields.PositiveIntegerField')(db_index=True)),
        ))
        db.send_create_signal(u'dispatcher', ['Entity'])

        # Adding model 'Topics'
        db.create_table(u'dispatcher_topics', (
            ('slug', self.gf('django.db.models.fields.CharField')(max_length=10, primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('category', self.gf('django.db.models.fields.CharField')(max_length=50)),
        ))
        db.send_create_signal(u'dispatcher', ['Topics'])

        # Adding model 'BlackList'
        db.create_table(u'dispatcher_blacklist', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('identity', self.gf('django.db.models.fields.CharField')(unique=True, max_length=30)),
            ('call_count', self.gf('django.db.models.fields.PositiveIntegerField')(default=1)),
        ))
        db.send_create_signal(u'dispatcher', ['BlackList'])


    def backwards(self, orm):
        # Removing unique constraint on 'HotlineEvent', fields ['identity', 'received_on']
        db.delete_unique(u'dispatcher_hotlineevent', ['identity', 'received_on'])

        # Deleting model 'HotlineEvent'
        db.delete_table(u'dispatcher_hotlineevent')

        # Deleting model 'HotlineVolunteer'
        db.delete_table(u'dispatcher_hotlinevolunteer')

        # Removing M2M table for field groups on 'HotlineVolunteer'
        db.delete_table(db.shorten_name(u'dispatcher_hotlinevolunteer_groups'))

        # Removing M2M table for field user_permissions on 'HotlineVolunteer'
        db.delete_table(db.shorten_name(u'dispatcher_hotlinevolunteer_user_permissions'))

        # Deleting model 'HotlineResponse'
        db.delete_table(u'dispatcher_hotlineresponse')

        # Removing M2M table for field topics on 'HotlineResponse'
        db.delete_table(db.shorten_name(u'dispatcher_hotlineresponse_topics'))

        # Deleting model 'Entity'
        db.delete_table(u'dispatcher_entity')

        # Deleting model 'Topics'
        db.delete_table(u'dispatcher_topics')

        # Deleting model 'BlackList'
        db.delete_table(u'dispatcher_blacklist')


    models = {
        u'auth.group': {
            'Meta': {'object_name': 'Group'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'auth.permission': {
            'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'dispatcher.blacklist': {
            'Meta': {'object_name': 'BlackList'},
            'call_count': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'identity': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        u'dispatcher.entity': {
            'Meta': {'object_name': 'Entity'},
            'latitude': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'level': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'lft': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'longitude': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'parent': ('mptt.fields.TreeForeignKey', [], {'blank': 'True', 'related_name': "u'children'", 'null': 'True', 'to': u"orm['dispatcher.Entity']"}),
            'rght': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'slug': ('django.db.models.fields.CharField', [], {'max_length': '20', 'primary_key': 'True'}),
            'tree_id': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '30'})
        },
        u'dispatcher.hotlineevent': {
            'Meta': {'unique_together': "[(u'identity', u'received_on')]", 'object_name': 'HotlineEvent'},
            'archived': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'created_on': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'event_type': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'hotline_number': ('django.db.models.fields.CharField', [], {'max_length': '30', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'identity': ('django.db.models.fields.CharField', [], {'max_length': '30'}),
            'operator': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'processed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'received_on': ('django.db.models.fields.DateTimeField', [], {}),
            'sms_message': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'volunteer': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['dispatcher.HotlineVolunteer']", 'null': 'True', 'blank': 'True'})
        },
        u'dispatcher.hotlineresponse': {
            'Meta': {'object_name': 'HotlineResponse'},
            'age': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'created_on': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'duration': ('django.db.models.fields.PositiveIntegerField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'location': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['dispatcher.Entity']", 'null': 'True', 'blank': 'True'}),
            'request': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['dispatcher.HotlineEvent']", 'unique': 'True'}),
            'response_date': ('django.db.models.fields.DateTimeField', [], {}),
            'sex': ('django.db.models.fields.CharField', [], {'default': "u'U'", 'max_length': "u'1'"}),
            'topics': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "u'responses'", 'symmetrical': 'False', 'to': u"orm['dispatcher.Topics']"})
        },
        u'dispatcher.hotlinevolunteer': {
            'Meta': {'object_name': 'HotlineVolunteer'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'operator': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'phone_number': ('django.db.models.fields.CharField', [], {'max_length': '30', 'null': 'True', 'blank': 'True'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        u'dispatcher.topics': {
            'Meta': {'object_name': 'Topics'},
            'category': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'slug': ('django.db.models.fields.CharField', [], {'max_length': '10', 'primary_key': 'True'})
        }
    }

    complete_apps = ['dispatcher']