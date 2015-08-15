# -*- coding: utf-8 -*-
from Products.Five.browser import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.CMFCore.utils import getToolByName
from Acquisition import aq_inner
from plone.memoize.instance import memoize
from lxml import etree
from mediawiki import wiki2html
import re
import logging
from zope.site.hooks import getSite
from zope.component import queryUtility
from plone.i18n.normalizer.interfaces import IIDNormalizer

from zope.component import getUtility
from plone.registry.interfaces import IRegistry
#Libs python
from suds.client import Client
from lx.tools import toolsMessageFactory as _


class LxToolsView(BrowserView):
    """Lx Tools"""

    __call__ = ViewPageTemplateFile('templates/lxtools.pt')

    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.errors = {}

    def settings(self):
        if 'form.action.reindexIndexObject' in self.request.form:
            tipo_conteudo = self.request.get('tipo.conteudo', None)
            index_conteudo = self.request.get('index.conteudo', None)
            if self.validateReindexIndex(tipo_conteudo, index_conteudo):
                return self.reindexIndexObject(tipo_conteudo, index_conteudo)


    def validateReindexIndex(self, tipo_conteudo, index_conteudo):
        """Validação do Reindex.
        """
        context = aq_inner(self.context)
        utils = getToolByName(context, 'plone_utils')
        if tipo_conteudo == None:
            self.errors['tipo_conteudo'] = "O campo é obrigatório."
        if index_conteudo == None:
            self.errors['index_conteudo'] = "O campo é obrigatório."
        # Check for errors
        if self.errors:
            utils.addPortalMessage("Corrija os erros.", type='error')
            return False
        else:
            return True

    def reindexIndexObject(self, tipo_conteudo, index_conteudo):
        """Reindex.
        """
        context = aq_inner(self.context)
        utils = getToolByName(context, 'plone_utils')
        ctool = getToolByName(self, 'portal_catalog')
        objects = ctool(portal_type=tipo_conteudo, sort_on='id', sort_order='ascending')
        log = logging.getLogger('REINDEX:')
        for object in objects:
            obj = object.getObject()
            try:
                obj.reindexObject(idxs=index_conteudo)
                log.info(obj.absolute_url_path() + ' CATALOGADO')
            except:
                log.info(obj.absolute_url_path() + ' ERRO')
        msg = 'Procedimento executado.'
        utils.addPortalMessage(msg, type='info')

    @memoize
    def getTypes(self):
        """
        """
        putils = getToolByName(self, 'plone_utils')
        allTypes = putils.getUserFriendlyTypes()
        allTypes = allTypes
        return sorted(allTypes, key=str.lower)

    @memoize
    def getIndexes(self):
        """Retorna todos os indices do catalog.
        """
        ctool = getToolByName(self, 'portal_catalog')
        indexs = ctool.getIndexObjects()
        indexs = [i.getId() for i in indexs]
        return sorted(indexs, key=str.lower)
