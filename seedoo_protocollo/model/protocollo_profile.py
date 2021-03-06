# -*- coding: utf-8 -*-
# This file is part of Seedoo.  The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.
import logging
from openerp import SUPERUSER_ID, api
from openerp.osv import orm, fields
from openerp.tools import GettextAlias

_logger = logging.getLogger(__name__)

_ = GettextAlias()


class ProtocolloProfile(orm.Model):
    _name = 'protocollo.profile'

    _columns = {

        'name': fields.char(size=256, string='Nome'),
        'groups_id': fields.many2many('res.groups', 'res_groups_profile_rel', 'uid', 'gid', 'Permessi'),
        'user_ids': fields.one2many('res.users', 'profile_id', 'Utenti'),
        'state': fields.selection(
            [
                ('enabled', 'Attivo'),
                ('disabled', 'Disattivo'),
            ], 'Stato'),
    }

    _defaults = {
        'state': 'enabled',
    }

    _order = 'name'

    def copy(self, cr, uid, id, default=None, context=None):
        profile_name = self.read(cr, uid, [id], ['name'])[0]['name']
        default.update({'name': _('%s (copy)') % profile_name})
        return super(ProtocolloProfile, self).copy(cr, uid, id, default, context)

    def write(self, cr, uid, ids, vals, context=None):
        old_profile_group_ids = {}

        if vals and vals.has_key('groups_id') and vals['groups_id']:
            for profile in self.browse(cr, uid, ids):
                old_profile_group_ids[profile.id] = profile.groups_id.ids

        super(ProtocolloProfile, self).write(cr, uid, ids, vals, context=context)

        if vals and vals.has_key('groups_id') and vals['groups_id']:
            for profile in self.browse(cr, uid, ids):
                user_ids = profile.user_ids.ids
                for user_id in user_ids:
                    self.associate_profile_to_user(cr, uid, profile, old_profile_group_ids[profile.id], user_id)

        return True

    def associate_profile_to_user(self, cr, uid, profile, old_profile_group_ids, user_id):
        group_id_value = []
        user_obj = self.pool.get('res.users')

        # (3, ID) delete the link
        delete_protocollo_group_ids = list(set(old_profile_group_ids))
        if profile:
            delete_protocollo_group_ids = list(set(old_profile_group_ids) - set(profile.groups_id.ids))
        if delete_protocollo_group_ids:
            for group_id in delete_protocollo_group_ids:
                group_id_value.append((3, group_id))

        # (4, ID) add the link
        add_protocollo_group_ids = []
        if profile:
            add_protocollo_group_ids = list(set(profile.groups_id.ids) - set(old_profile_group_ids))
        if add_protocollo_group_ids:
            for group_id in add_protocollo_group_ids:
                group_id_value.append((4, group_id))

        if group_id_value:
            user_obj.write(cr, uid, [user_id], {
                'groups_id': group_id_value
            })